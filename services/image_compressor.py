"""
Механизм сжатия изображений.

Реализует адаптивный алгоритм сжатия:
- Автоматическое определение формата по расширению
- Конвертация неподдерживаемых форматов (HEIC, BMP, TIFF) в JPEG/WebP
- Динамический выбор степени сжатия на основе анализа размера и разрешения
- Интеллектуальный ресемплинг (Lanczos) до 1280-1600px по длинной стороне
- Сохранение EXIF-метаданных
- Поддержка прозрачности (альфа-канал) через WebP
- Пакетная обработка с асинхронной очередью и прогресс-баром
- Пресеты: "Максимальное качество", "Сбалансированно", "Экономия трафика"
- Без потери качества для малых изображений (< 256x256 или < 100 КБ)
- Корректная обработка Progressive JPEG и анимированных GIF/WebP
"""

import os
import io
import sys
import time
import copy
import logging
import shutil
import argparse
from contextlib import contextmanager
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple, List, Dict, Union, BinaryIO, Callable
from enum import Enum
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed

from PIL import Image, ImageOps, ImageSequence

# Константа для безопасного лимита Pillow.
# Достаточно для самого большого пресета MAX_QUALITY (2560x2560).
# Лимит устанавливается в __init__ компрессора, чтобы не мутировать
# глобальное состояние при импорте модуля.
SAFE_PIXEL_LIMIT = 2560 * 2560 * 4

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────
# Константы и перечисления
# ──────────────────────────────────────────────────────────────────────

# Расширения, сгруппированные по категориям
RASTER_FORMATS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff', '.tif', '.gif'}
HEIF_FORMATS = {'.heic', '.heif', '.avif'}
VECTOR_FORMATS = {'.svg'}
ALL_IMAGE_FORMATS = RASTER_FORMATS | HEIF_FORMATS | VECTOR_FORMATS

# Форматы, поддерживающие анимацию
ANIMATED_FORMATS = {'.gif', '.webp'}

# Форматы с альфа-каналом
ALPHA_FORMATS = {'.png', '.webp', '.gif'}

# Форматы, поддерживающие EXIF
EXIF_FORMATS = {'.jpg', '.jpeg', '.tiff', '.tif'}

# Форматы, в которые можно сохранять
OUTPUT_FORMATS = {
    '.jpg': 'JPEG',
    '.jpeg': 'JPEG',
    '.png': 'PNG',
    '.webp': 'WebP',
    '.gif': 'GIF',
}

# Разрешённые расширения для вывода
ALLOWED_OUTPUT_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}


class CompressionPreset(Enum):
    """Пресеты сжатия"""
    MAX_QUALITY = "max_quality"
    BALANCED = "balanced"
    TRAFFIC_SAVING = "traffic_saving"


@dataclass
class CompressionConfig:
    """Конфигурация сжатия"""
    preset: CompressionPreset = CompressionPreset.BALANCED
    max_long_side: int = 1280
    jpeg_quality: int = 88
    webp_quality: int = 88
    target_max_size: int = 600 * 1024
    skip_threshold_bytes: int = 100 * 1024
    skip_threshold_pixels: int = 256 * 256
    keep_exif: bool = True
    keep_alpha: bool = True
    max_workers: int = 4

    def apply_preset(self, preset: CompressionPreset) -> None:
        """Применить предустановленные параметры.
        
        Сбрасывает все поля конфигурации к значениям выбранного пресета.
        Поля keep_exif, keep_alpha и max_workers не затрагиваются,
        так как они не зависят от пресета.
        """
        self.preset = preset
        if preset == CompressionPreset.MAX_QUALITY:
            self.max_long_side = 2560
            self.jpeg_quality = 95
            self.webp_quality = 95
            self.target_max_size = 1024 * 1024
            self.skip_threshold_bytes = 50 * 1024
            self.skip_threshold_pixels = 128 * 128
        elif preset == CompressionPreset.BALANCED:
            self.max_long_side = 1280
            self.jpeg_quality = 88
            self.webp_quality = 88
            self.target_max_size = 600 * 1024
            self.skip_threshold_bytes = 100 * 1024
            self.skip_threshold_pixels = 256 * 256
        elif preset == CompressionPreset.TRAFFIC_SAVING:
            self.max_long_side = 800
            self.jpeg_quality = 65
            self.webp_quality = 65
            self.target_max_size = 300 * 1024
            self.skip_threshold_bytes = 200 * 1024
            self.skip_threshold_pixels = 512 * 512


class CompressionError(Exception):
    """Базовое исключение для ошибок сжатия"""
    pass


class UnsupportedFormatError(CompressionError):
    """Неподдерживаемый формат файла"""
    pass


class ConversionError(CompressionError):
    """Ошибка конвертации формата"""
    pass


@dataclass
class CompressionResult:
    """Результат сжатия одного файла"""
    source_path: Path
    output_path: Path
    original_size: int
    compressed_size: int
    original_format: str
    output_format: str
    original_dimensions: Tuple[int, int]
    compressed_dimensions: Tuple[int, int]
    compression_ratio: float
    was_resized: bool
    was_converted: bool
    exif_preserved: bool
    processing_time: float
    error: Optional[str] = None
    skipped: bool = False

    @property
    def saved_bytes(self) -> int:
        return self.original_size - self.compressed_size

    @property
    def saved_percent(self) -> float:
        if self.original_size == 0:
            return 0.0
        return (1 - self.compressed_size / self.original_size) * 100


class ImageCompressor:
    """
    Компрессор изображений.

    Особенности:
    - Автоматическое определение формата по расширению
    - Конвертация HEIC/HEIF/AVIF/BMP/TIFF в JPEG или WebP
    - Адаптивное сжатие с ресайзом до 1280px по длинной стороне
    - Сохранение EXIF
    - Поддержка прозрачности через WebP
    - Пакетная обработка с прогресс-баром
    - Три пресета: max_quality, balanced, traffic_saving
    """

    def __init__(self, config: Optional[CompressionConfig] = None):
        self.config = config or CompressionConfig()
        self._heif_available = self._check_heif_support()

    @staticmethod
    @contextmanager
    def _pixel_limit_context():
        """Контекстный менеджер для безопасного увеличения лимита Pillow.
        
        Используется внутри compress/compress_bytes вместо мутации
        глобального состояния в __init__/__del__, что исключает
        проблемы с многопоточностью и ненадёжным вызовом __del__.
        """
        original = Image.MAX_IMAGE_PIXELS
        Image.MAX_IMAGE_PIXELS = max(original, SAFE_PIXEL_LIMIT)
        try:
            yield
        finally:
            Image.MAX_IMAGE_PIXELS = original

    @staticmethod
    def _check_heif_support() -> bool:
        try:
            import pillow_heif  # noqa: F401
            return True
        except ImportError:
            return False

    @staticmethod
    def is_supported_input(ext: str) -> bool:
        return ext.lower() in ALL_IMAGE_FORMATS

    @staticmethod
    def is_supported_output(ext: str) -> bool:
        return ext.lower() in ALLOWED_OUTPUT_EXTENSIONS

    # ── Загрузка изображения ─────────────────────────────────────────

    def _load_image(self, filepath: Path) -> Tuple[Image.Image, Optional[bytes]]:
        ext = filepath.suffix.lower()

        if ext in HEIF_FORMATS:
            return self._load_heif(filepath)

        if ext == '.svg':
            return self._load_svg(filepath)

        try:
            with Image.open(filepath) as img:
                img.load()

                exif_data = None
                if ext in EXIF_FORMATS:
                    try:
                        exif_data = img.info.get('exif')
                    except Exception as e:
                        logger.debug("Failed to read EXIF from %s: %s", filepath, e)

                if ext in ANIMATED_FORMATS:
                    return self._load_animated(img, filepath, exif_data)

                return img, exif_data

        except Image.DecompressionBombError:
            raise CompressionError(
                f"Изображение слишком большое: {filepath}. "
                f"Увеличьте Image.MAX_IMAGE_PIXELS или используйте меньшее изображение."
            )
        except Exception as e:
            raise CompressionError(f"Не удалось загрузить изображение {filepath}: {e}")

    def _load_heif(self, filepath: Path) -> Tuple[Image.Image, Optional[bytes]]:
        if not self._heif_available:
            raise ConversionError(
                "Библиотека pillow-heif не установлена. "
                "Установите: pip install pillow-heif"
            )

        try:
            import pillow_heif

            heif_file = pillow_heif.open_heif(filepath)
            img = Image.frombytes(
                heif_file.mode,
                heif_file.size,
                heif_file.data,
                "raw",
                heif_file.mode,
                heif_file.stride,
            )

            # Проверка на превышение лимита пикселей
            if img.size[0] * img.size[1] > Image.MAX_IMAGE_PIXELS:
                raise Image.DecompressionBombError(
                    f"Изображение слишком большое: {filepath}"
                )

            exif_data = None
            try:
                exif_data = heif_file.info.get('exif')
            except Exception:
                pass

            return img, exif_data

        except Image.DecompressionBombError:
            raise CompressionError(
                f"Изображение слишком большое: {filepath}. "
                f"Увеличьте Image.MAX_IMAGE_PIXELS или используйте меньшее изображение."
            )
        except Exception as e:
            raise ConversionError(f"Не удалось загрузить HEIC {filepath}: {e}")

    def _load_svg(self, filepath: Path) -> Tuple[Image.Image, Optional[bytes]]:
        try:
            import cairosvg
            png_data = cairosvg.svg2png(url=str(filepath))
            img = Image.open(io.BytesIO(png_data))
            img.load()
            # Проверка на превышение лимита пикселей
            if img.size[0] * img.size[1] > Image.MAX_IMAGE_PIXELS:
                raise Image.DecompressionBombError(
                    f"SVG слишком большой после конвертации: {filepath}"
                )
            return img, None

        except Image.DecompressionBombError:
            raise CompressionError(
                f"SVG слишком большой после конвертации: {filepath}. "
                f"Увеличьте Image.MAX_IMAGE_PIXELS или используйте меньшее изображение."
            )
        except ImportError:
            try:
                import subprocess
                resolved_path = filepath.resolve()
                if not resolved_path.exists():
                    raise ConversionError(f"Файл SVG не найден: {filepath}")
                # Безопасность: проверяем, что путь не выходит за пределы
                # рабочей директории (защита от path traversal)
                cwd = Path.cwd().resolve()
                if cwd not in resolved_path.parents and resolved_path != cwd:
                    raise ConversionError(
                        f"Недопустимый путь к SVG-файлу (выход за пределы рабочей директории): {filepath}"
                    )
                result = subprocess.run(
                    ['rsvg-convert', '--format', 'png', str(resolved_path)],
                    capture_output=True, timeout=30
                )
                if result.returncode == 0:
                    img = Image.open(io.BytesIO(result.stdout))
                    img.load()
                    # Проверка на превышение лимита пикселей
                    if img.size[0] * img.size[1] > Image.MAX_IMAGE_PIXELS:
                        raise Image.DecompressionBombError(
                            f"SVG слишком большой после конвертации: {filepath}"
                        )
                    return img, None
            except Image.DecompressionBombError:
                raise CompressionError(
                    f"SVG слишком большой после конвертации: {filepath}. "
                    f"Увеличьте Image.MAX_IMAGE_PIXELS или используйте меньшее изображение."
                )
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass

            raise ConversionError(
                "Не удалось загрузить SVG. Установите cairosvg: pip install cairosvg"
            )

    def _load_animated(
        self, img: Image.Image, filepath: Path, exif_data: Optional[bytes]
    ) -> Tuple[Image.Image, Optional[bytes]]:
        frames = []
        duration = []
        try:
            for frame in ImageSequence.Iterator(img):
                frames.append(frame.copy())
                duration.append(frame.info.get('duration', 100))
        except Exception:
            frames = [img.copy()]
            duration = [100]

        img.info['_frames'] = frames
        img.info['_duration'] = duration
        img.info['_is_animated'] = True

        return img, exif_data

    # ── Определение необходимости обработки ──────────────────────────

    def _should_skip(self, img: Image.Image, file_size: int) -> bool:
        width, height = img.size
        pixel_count = width * height

        # Пропускаем сжатие только если изображение МАЛЕНЬКОЕ И по размерам, И по файлу.
        # Если изображение большое по размерам, но маленькое по файлу (например,
        # простой PNG 800x600), оно всё равно должно быть обработано.
        if pixel_count < self.config.skip_threshold_pixels and file_size < self.config.skip_threshold_bytes:
            return True

        return False

    def _needs_resize(self, img: Image.Image) -> bool:
        width, height = img.size
        long_side = max(width, height)
        return long_side > self.config.max_long_side

    def _needs_conversion(self, ext: str) -> Optional[str]:
        ext = ext.lower()

        if ext in HEIF_FORMATS or ext in {'.bmp', '.tiff', '.tif', '.avif'}:
            return '.jpg'

        if ext == '.svg':
            return '.png'

        return None

    def _determine_output_format(
        self, img: Image.Image, source_ext: str, target_ext: Optional[str] = None
    ) -> str:
        has_alpha = img.mode in ('RGBA', 'LA', 'PA') or (
            img.mode == 'P' and 'transparency' in img.info
        )

        if target_ext:
            if target_ext in ALLOWED_OUTPUT_EXTENSIONS:
                return target_ext
            return '.jpg'

        conversion_target = self._needs_conversion(source_ext)
        if conversion_target:
            if has_alpha and self.config.keep_alpha:
                return '.webp'
            return conversion_target

        if source_ext == '.png' and has_alpha and self.config.keep_alpha:
            return '.webp'

        if source_ext in ANIMATED_FORMATS:
            return source_ext

        if source_ext in ALLOWED_OUTPUT_EXTENSIONS:
            return source_ext

        return '.jpg'

    # ── Ресемплинг ───────────────────────────────────────────────────

    def _resize_image(
        self, img: Image.Image, target_long_side: Optional[int] = None
    ) -> Image.Image:
        if target_long_side is None:
            target_long_side = self.config.max_long_side

        width, height = img.size
        long_side = max(width, height)

        if long_side <= target_long_side:
            return img

        ratio = target_long_side / long_side
        new_width = int(width * ratio)
        new_height = int(height * ratio)

        return img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # ── Обработка EXIF ───────────────────────────────────────────────

    @staticmethod
    def _apply_exif_orientation(img: Image.Image) -> Image.Image:
        try:
            return ImageOps.exif_transpose(img) or img
        except Exception:
            return img

    @staticmethod
    def _extract_exif_bytes(img: Image.Image) -> Optional[bytes]:
        try:
            exif_data = img.info.get('exif')
            if exif_data:
                return exif_data
        except Exception:
            pass
        return None

    @staticmethod
    def _strip_exif(img: Image.Image) -> Image.Image:
        if 'exif' in img.info:
            del img.info['exif']
        return img

    # ── Обработка альфа-канала ───────────────────────────────────────

    @staticmethod
    def _remove_alpha(img: Image.Image, background_color: Tuple[int, int, int] = (255, 255, 255)) -> Image.Image:
        if img.mode in ('RGBA', 'LA'):
            background = Image.new('RGB', img.size, background_color)
            if img.mode == 'RGBA':
                background.paste(img, mask=img.split()[3])
            else:
                background.paste(img, mask=img.split()[1])
            return background
        elif img.mode == 'P':
            # Прямая конвертация P -> RGB с указанием цвета фона
            return img.convert('RGB')
        return img.convert('RGB')

    # ── Адаптивный подбор качества ───────────────────────────────────

    def _adaptive_quality_search(
        self, img: Image.Image, output_format: str, output_ext: str,
        target_size: int, min_quality: int = 50, max_quality: int = 95
    ) -> Tuple[int, Optional[bytes]]:
        """Бинарный поиск оптимального качества.

        Returns:
            Tuple[int, Optional[bytes]]: (лучшее_качество, закодированные_данные_последней_итерации)
        """
        if output_ext == '.png':
            return 100, None

        low, high = min_quality, max_quality
        best_quality = high
        best_data = None

        while low <= high:
            mid = (low + high) // 2
            data = self._encode_image(img, output_format, mid)

            if data is None:
                high = mid - 1
                continue

            size = len(data)

            if size <= target_size:
                best_quality = mid
                best_data = data
                low = mid + 1
            else:
                high = mid - 1

        return best_quality, best_data

    def _encode_image(self, img: Image.Image, output_format: str, quality: int) -> Optional[bytes]:
        """Закодировать изображение в байты с заданным качеством."""
        buffer = io.BytesIO()
        save_kwargs = {'format': output_format, 'quality': quality}

        if output_format == 'WebP':
            save_kwargs['method'] = 6

        try:
            img.save(buffer, **save_kwargs)
            return buffer.getvalue()
        except Exception:
            return None

    # ── Сохранение изображения ───────────────────────────────────────

    def _build_save_kwargs(
        self,
        output_ext: str,
        exif_data: Optional[bytes] = None,
        quality: Optional[int] = None,
        animated: bool = False,
        img: Optional[Image.Image] = None,
    ) -> Dict:
        """Построить словарь параметров для сохранения изображения.

        Args:
            output_ext: Расширение выходного файла
            exif_data: EXIF-данные для сохранения
            quality: Качество сжатия (для JPEG/WebP)
            animated: Флаг анимированного изображения
            img: Объект изображения (требуется для GIF с кадрами)

        Returns:
            Dict: Параметры для передачи в img.save()
        """
        output_format = OUTPUT_FORMATS.get(output_ext, 'JPEG')

        if quality is None:
            if output_ext == '.jpg':
                quality = self.config.jpeg_quality
            elif output_ext == '.webp':
                quality = self.config.webp_quality
            else:
                quality = 100

        save_kwargs: Dict = {'format': output_format}

        if output_format == 'JPEG':
            save_kwargs['quality'] = quality
            save_kwargs['optimize'] = True
            save_kwargs['progressive'] = True
            if exif_data and self.config.keep_exif:
                save_kwargs['exif'] = exif_data

        elif output_format == 'WebP':
            save_kwargs['quality'] = quality
            save_kwargs['method'] = 6
            if exif_data and self.config.keep_exif:
                save_kwargs['exif'] = exif_data

        elif output_format == 'PNG':
            save_kwargs['optimize'] = True
            if exif_data and self.config.keep_exif:
                save_kwargs['exif'] = exif_data

        elif output_format == 'GIF':
            if animated and img is not None and '_frames' in img.info:
                frames = img.info['_frames']
                duration = img.info.get('_duration', [100] * len(frames))
                save_kwargs['save_all'] = True
                save_kwargs['append_images'] = frames[1:]
                save_kwargs['duration'] = duration
                save_kwargs['loop'] = 0
                save_kwargs['optimize'] = True
            else:
                save_kwargs['optimize'] = True

        return save_kwargs

    def _save_image(
        self,
        img: Image.Image,
        output_path: Path,
        output_ext: str,
        exif_data: Optional[bytes] = None,
        quality: Optional[int] = None,
        animated: bool = False,
    ) -> int:
        save_kwargs = self._build_save_kwargs(
            output_ext, exif_data=exif_data, quality=quality,
            animated=animated, img=img,
        )

        try:
            output_format = OUTPUT_FORMATS.get(output_ext, 'JPEG')
            if output_format == 'GIF' and animated and '_frames' in img.info:
                frames = img.info['_frames']
                frames[0].save(str(output_path), **save_kwargs)
            else:
                img.save(str(output_path), **save_kwargs)

            return output_path.stat().st_size

        except Exception as e:
            raise CompressionError(f"Не удалось сохранить изображение {output_path}: {e}")

    # ── Основной метод сжатия одного файла ───────────────────────────

    def compress(
        self,
        source_path: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None,
        output_ext: Optional[str] = None,
        preset: Optional[CompressionPreset] = None,
        **kwargs
    ) -> CompressionResult:
        start_time = time.time()

        source_path = Path(source_path)
        if not source_path.exists():
            raise FileNotFoundError(f"Файл не найден: {source_path}")

        with self._pixel_limit_context():
            return self._compress_impl(
                source_path, output_path, output_ext, preset, **kwargs
            )

    def _compress_impl(
        self,
        source_path: Path,
        output_path: Optional[Union[str, Path]] = None,
        output_ext: Optional[str] = None,
        preset: Optional[CompressionPreset] = None,
        **kwargs
    ) -> CompressionResult:

        source_ext = source_path.suffix.lower()
        original_size = source_path.stat().st_size

        # Создаём локальную копию конфига для потокобезопасности
        config = copy.deepcopy(self.config)
        if preset:
            config.apply_preset(preset)

        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)

        img, exif_data = self._load_image(source_path)
        original_dims = img.size

        is_animated = img.info.get('_is_animated', False)

        if self._should_skip(img, original_size) and not is_animated:
            if output_path:
                output_path = Path(output_path)
                # Защита от копирования файла самого в себя
                if output_path.resolve() == source_path.resolve():
                    compressed_size = original_size
                else:
                    if output_path.exists():
                        logger.warning(
                            "Output path already exists, overwriting: %s", output_path
                        )
                    shutil.copy2(source_path, output_path)
                    compressed_size = output_path.stat().st_size
            else:
                compressed_size = original_size
                output_path = source_path

            return CompressionResult(
                source_path=source_path,
                output_path=output_path,
                original_size=original_size,
                compressed_size=compressed_size,
                original_format=source_ext,
                output_format=source_ext,
                original_dimensions=original_dims,
                compressed_dimensions=original_dims,
                compression_ratio=1.0,
                was_resized=False,
                was_converted=False,
                exif_preserved=True,
                processing_time=time.time() - start_time,
                skipped=True,
            )

        if exif_data and config.keep_exif:
            img = self._apply_exif_orientation(img)

        if output_ext:
            output_ext = output_ext.lower()
        elif output_path:
            output_path_parsed = Path(output_path)
            if not output_path_parsed.is_dir():
                output_ext = output_path_parsed.suffix.lower()
            else:
                output_ext = self._determine_output_format(img, source_ext)
        else:
            output_ext = self._determine_output_format(img, source_ext)

        was_converted = output_ext != source_ext

        was_resized = self._needs_resize(img)
        if was_resized:
            img = self._resize_image(img)

        has_alpha = img.mode in ('RGBA', 'LA', 'PA') or (
            img.mode == 'P' and 'transparency' in img.info
        )

        if has_alpha:
            if output_ext == '.webp' and config.keep_alpha:
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
            elif output_ext == '.png':
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
            else:
                img = self._remove_alpha(img)
        elif output_ext in ('.jpg', '.jpeg'):
            if img.mode != 'RGB':
                img = img.convert('RGB')

        output_format = OUTPUT_FORMATS.get(output_ext, 'JPEG')

        pre_encoded_data = None
        if output_ext in ('.jpg', '.jpeg', '.webp'):
            quality, pre_encoded_data = self._adaptive_quality_search(
                img, output_format, output_ext,
                target_size=config.target_max_size,
                min_quality=50 if config.preset != CompressionPreset.MAX_QUALITY else 80,
                max_quality=config.jpeg_quality if output_ext in ('.jpg', '.jpeg') else config.webp_quality,
            )
        else:
            quality = 100

        if output_path:
            output_path = Path(output_path)
            if output_path.is_dir():
                output_path = output_path / f"{source_path.stem}{output_ext}"
        else:
            output_path = source_path.parent / f"{source_path.stem}{output_ext}"

        output_path.parent.mkdir(parents=True, exist_ok=True)

        if pre_encoded_data is not None:
            # Используем уже закодированные данные из адаптивного поиска
            output_path.write_bytes(pre_encoded_data)
            compressed_size = len(pre_encoded_data)
        else:
            compressed_size = self._save_image(
                img, output_path, output_ext,
                exif_data=exif_data if config.keep_exif else None,
                quality=quality,
                animated=is_animated,
            )

        processing_time = time.time() - start_time
        compression_ratio = compressed_size / original_size if original_size > 0 else 1.0

        return CompressionResult(
            source_path=source_path,
            output_path=output_path,
            original_size=original_size,
            compressed_size=compressed_size,
            original_format=source_ext,
            output_format=output_ext,
            original_dimensions=original_dims,
            compressed_dimensions=img.size,
            compression_ratio=compression_ratio,
            was_resized=was_resized,
            was_converted=was_converted,
            exif_preserved=config.keep_exif and exif_data is not None,
            processing_time=processing_time,
        )

    # ── Сжатие из байтов ─────────────────────────────────────────────

    def compress_bytes(
        self,
        data: bytes,
        source_ext: str,
        output_ext: Optional[str] = None,
        **kwargs
    ) -> Tuple[bytes, Dict]:
        start_time = time.time()

        source_ext = source_ext.lower()
        original_size = len(data)

        # Создаём локальную копию конфига для потокобезопасности
        config = copy.deepcopy(self.config)
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)

        with self._pixel_limit_context():
            return self._compress_bytes_impl(data, source_ext, output_ext, config, start_time)

    def _compress_bytes_impl(
        self,
        data: bytes,
        source_ext: str,
        output_ext: Optional[str],
        config: CompressionConfig,
        start_time: float,
    ) -> Tuple[bytes, Dict]:
        try:
            img = Image.open(io.BytesIO(data))
            img.load()
        except Exception as e:
            raise CompressionError(f"Не удалось загрузить изображение из байтов: {e}")

        original_dims = img.size
        exif_data = self._extract_exif_bytes(img)

        if self._should_skip(img, original_size):
            return data, {
                'skipped': True,
                'original_size': original_size,
                'compressed_size': original_size,
                'original_dimensions': original_dims,
                'compressed_dimensions': original_dims,
            }

        if exif_data and config.keep_exif:
            img = self._apply_exif_orientation(img)

        if output_ext:
            output_ext = output_ext.lower()
        else:
            output_ext = self._determine_output_format(img, source_ext)

        was_converted = output_ext != source_ext

        was_resized = self._needs_resize(img)
        if was_resized:
            img = self._resize_image(img)

        has_alpha = img.mode in ('RGBA', 'LA', 'PA') or (
            img.mode == 'P' and 'transparency' in img.info
        )
        if has_alpha:
            if output_ext == '.webp' and config.keep_alpha:
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
            elif output_ext == '.png':
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
            else:
                img = self._remove_alpha(img)
        elif output_ext in ('.jpg', '.jpeg'):
            if img.mode != 'RGB':
                img = img.convert('RGB')

        output_format = OUTPUT_FORMATS.get(output_ext, 'JPEG')
        pre_encoded_data = None
        if output_ext in ('.jpg', '.jpeg', '.webp'):
            quality, pre_encoded_data = self._adaptive_quality_search(
                img, output_format, output_ext,
                target_size=config.target_max_size,
            )
        else:
            quality = 100

        if pre_encoded_data is not None:
            compressed_data = pre_encoded_data
        else:
            buffer = io.BytesIO()
            save_kwargs = self._build_save_kwargs(
                output_ext, exif_data=exif_data if config.keep_exif else None,
                quality=quality,
            )
            img.save(buffer, **save_kwargs)
            compressed_data = buffer.getvalue()

        processing_time = time.time() - start_time

        return compressed_data, {
            'skipped': False,
            'original_size': original_size,
            'compressed_size': len(compressed_data),
            'original_format': source_ext,
            'output_format': output_ext,
            'original_dimensions': original_dims,
            'compressed_dimensions': img.size,
            'was_resized': was_resized,
            'was_converted': was_converted,
            'quality': quality,
            'processing_time': processing_time,
        }

    # ── Пакетная обработка ───────────────────────────────────────────

    def compress_batch(
        self,
        source_paths: List[Union[str, Path]],
        output_dir: Optional[Union[str, Path]] = None,
        output_ext: Optional[str] = None,
        preset: Optional[CompressionPreset] = None,
        progress_callback: Optional[Callable[[int, int, CompressionResult], None]] = None,
        **kwargs
    ) -> List[CompressionResult]:
        """
        Пакетная обработка изображений.

        ВНИМАНИЕ: Метод не предназначен для одновременного вызова из нескольких потоков
        с одним экземпляром ImageCompressor. Для многопоточного использования создавайте
        отдельный экземпляр ImageCompressor на поток или используйте внешний пул потоков.

        Args:
            source_paths: Список путей к изображениям
            output_dir: Директория для сохранения результатов
            output_ext: Целевое расширение для всех файлов
            preset: Пресет сжатия
            progress_callback: Функция обратного вызова (completed, total, result)
            **kwargs: Дополнительные параметры конфигурации

        Returns:
            List[CompressionResult]: Список результатов сжатия
        """
        results: List[CompressionResult] = []
        total = len(source_paths)
        completed = 0

        if total <= 2:
            for source_path in source_paths:
                source_path = Path(source_path)
                if output_dir:
                    out_path = Path(output_dir) / source_path.name
                else:
                    out_path = None

                try:
                    result = self.compress(
                        source_path,
                        output_path=out_path,
                        output_ext=output_ext,
                        preset=preset,
                        **kwargs
                    )
                except Exception as e:
                    result = CompressionResult(
                        source_path=source_path,
                        output_path=source_path,
                        original_size=0,
                        compressed_size=0,
                        original_format=source_path.suffix.lower(),
                        output_format=output_ext or source_path.suffix.lower(),
                        original_dimensions=(0, 0),
                        compressed_dimensions=(0, 0),
                        compression_ratio=1.0,
                        was_resized=False,
                        was_converted=False,
                        exif_preserved=False,
                        processing_time=0.0,
                        error=str(e),
                    )

                results.append(result)
                completed += 1
                if progress_callback:
                    progress_callback(completed, total, result)

            return results

        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            future_to_path = {}
            for source_path in source_paths:
                source_path = Path(source_path)
                if output_dir:
                    out_path = Path(output_dir) / source_path.name
                else:
                    out_path = None

                future = executor.submit(
                    self._compress_single_safe,
                    source_path, out_path, output_ext, preset, **kwargs
                )
                future_to_path[future] = source_path

            try:
                for future in as_completed(future_to_path, timeout=300):
                    try:
                        result = future.result()
                    except TimeoutError:
                        source_path = future_to_path[future]
                        result = CompressionResult(
                            source_path=source_path,
                            output_path=source_path,
                            original_size=0,
                            compressed_size=0,
                            original_format=source_path.suffix.lower(),
                            output_format=output_ext or source_path.suffix.lower(),
                            original_dimensions=(0, 0),
                            compressed_dimensions=(0, 0),
                            compression_ratio=1.0,
                            was_resized=False,
                            was_converted=False,
                            exif_preserved=False,
                            processing_time=0.0,
                            error=f"Timeout processing {source_path.name}",
                        )
                    except Exception as e:
                        source_path = future_to_path[future]
                        result = CompressionResult(
                            source_path=source_path,
                            output_path=source_path,
                            original_size=0,
                            compressed_size=0,
                            original_format=source_path.suffix.lower(),
                            output_format=output_ext or source_path.suffix.lower(),
                            original_dimensions=(0, 0),
                            compressed_dimensions=(0, 0),
                            compression_ratio=1.0,
                            was_resized=False,
                            was_converted=False,
                            exif_preserved=False,
                            processing_time=0.0,
                            error=str(e),
                        )

                    results.append(result)
                    completed += 1
                    if progress_callback:
                        progress_callback(completed, total, result)
            finally:
                # Отменяем оставшиеся задачи при таймауте или ошибке
                for future in future_to_path:
                    if not future.done():
                        future.cancel()
                # Явно завершаем executor с таймаутом (Python 3.9+)
                executor.shutdown(wait=False, cancel_futures=True)

        results.sort(key=lambda r: str(r.source_path))
        return results

    def _compress_single_safe(
        self,
        source_path: Path,
        output_path: Optional[Path] = None,
        output_ext: Optional[str] = None,
        preset: Optional[CompressionPreset] = None,
        **kwargs
    ) -> CompressionResult:
        return self.compress(
            source_path,
            output_path=output_path,
            output_ext=output_ext,
            preset=preset,
            **kwargs
        )

    @staticmethod
    def format_report(results: List[CompressionResult], detailed: bool = False) -> str:
        total_original = sum(r.original_size for r in results)
        total_compressed = sum(r.compressed_size for r in results)
        total_saved = total_original - total_compressed
        total_time = sum(r.processing_time for r in results)
        errors = [r for r in results if r.error]
        skipped = [r for r in results if r.skipped]

        lines = [
            "=" * 70,
            "ОТЧЁТ О СЖАТИИ ИЗОБРАЖЕНИЙ",
            "=" * 70,
            f"Всего файлов:         {len(results)}",
            f"  - успешно сжато:    {len(results) - len(errors) - len(skipped)}",
            f"  - пропущено (малые): {len(skipped)}",
            f"  - с ошибками:       {len(errors)}",
            "",
            f"Исходный размер:     {_format_size(total_original)}",
            f"Сжатый размер:       {_format_size(total_compressed)}",
            f"Сэкономлено:         {_format_size(total_saved)} ({_calc_percent(total_saved, total_original):.1f}%)",
            "",
            f"Общее время:         {total_time:.2f} сек",
            f"Среднее время:       {total_time / max(len(results), 1):.2f} сек/файл",
        ]

        if errors:
            lines.extend(["", "ОШИБКИ:", "-" * 70])
            for r in errors:
                lines.append(f"  {r.source_path.name}: {r.error}")

        if detailed:
            lines.extend(["", "ДЕТАЛЬНАЯ ИНФОРМАЦИЯ ПО КАЖДОМУ ФАЙЛУ:", "-" * 70])
            for r in results:
                status = "✓" if not r.error else "✗"
                skip_mark = " (пропущен)" if r.skipped else ""
                lines.append(
                    f"  {status} {r.source_path.name}{skip_mark}\n"
                    f"    {r.original_dimensions[0]}x{r.original_dimensions[1]} -> "
                    f"{r.compressed_dimensions[0]}x{r.compressed_dimensions[1]} | "
                    f"{_format_size(r.original_size)} -> {_format_size(r.compressed_size)} | "
                    f"{r.saved_percent:.1f}% | {r.processing_time:.2f}с"
                )

        lines.append("=" * 70)
        return "\n".join(lines)


# ──────────────────────────────────────────────────────────────────────
# Вспомогательные функции
# ──────────────────────────────────────────────────────────────────────

def _format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} Б"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} КБ"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} МБ"


def _calc_percent(part: int, total: int) -> float:
    if total == 0:
        return 0.0
    return (part / total) * 100


# ──────────────────────────────────────────────────────────────────────
# CLI-интерфейс
# ──────────────────────────────────────────────────────────────────────

def create_cli_parser() -> 'argparse.ArgumentParser':
    parser = argparse.ArgumentParser(
        description="Компрессор изображений",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры:
  %(prog)s photo.jpg
  %(prog)s -o compressed/ *.jpg *.png
  %(prog)s --preset traffic_saving -r input_dir/
  %(prog)s --preset max_quality image.heic
  %(prog)s --batch --output-dir ./out *.jpg *.heic
        """
    )

    parser.add_argument(
        'files', nargs='+',
        help='Пути к файлам или директориям для сжатия'
    )

    parser.add_argument(
        '-o', '--output', '--output-dir',
        dest='output_dir',
        default=None,
        help='Директория для сохранения результатов'
    )

    parser.add_argument(
        '--output-ext',
        default=None,
        choices=['.jpg', '.jpeg', '.png', '.webp'],
        help='Целевое расширение для всех файлов'
    )

    parser.add_argument(
        '--preset',
        default='balanced',
        choices=['max_quality', 'balanced', 'traffic_saving'],
        help='Пресет сжатия (умолчание: balanced)'
    )

    parser.add_argument(
        '--max-long-side',
        type=int,
        default=None,
        help='Максимальная длинная сторона в пикселях'
    )

    parser.add_argument(
        '--quality',
        type=int,
        default=None,
        help='Качество JPEG/WebP (1-100)'
    )

    parser.add_argument(
        '--target-size',
        type=int,
        default=None,
        help='Целевой максимальный размер в КБ'
    )

    parser.add_argument(
        '--no-exif',
        action='store_true',
        help='Не сохранять EXIF-метаданные'
    )

    parser.add_argument(
        '--no-alpha',
        action='store_true',
        help='Удалить альфа-канал (конвертировать в JPEG)'
    )

    parser.add_argument(
        '-r', '--recursive',
        action='store_true',
        help='Рекурсивный поиск файлов в директориях'
    )

    parser.add_argument(
        '--batch',
        action='store_true',
        help='Пакетный режим (многопоточная обработка)'
    )

    parser.add_argument(
        '--workers',
        type=int,
        default=4,
        choices=range(1, 33),
        metavar='[1-32]',
        help='Количество потоков для пакетной обработки (1-32)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Пробный запуск без фактического сжатия'
    )

    parser.add_argument(
        '--detailed',
        action='store_true',
        help='Подробный отчёт по каждому файлу'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Подробный вывод в процессе работы'
    )

    return parser


def cli_main(argv: Optional[List[str]] = None) -> int:
    """
    Точка входа для CLI.
    Возвращает код возврата (0 = успех, 1 = ошибка).
    """
    parser = create_cli_parser()
    args = parser.parse_args(argv)

    log_level = logging.DEBUG if args.verbose else logging.WARNING
    logging.getLogger().setLevel(log_level)
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%H:%M:%S'
        )

    # Валидация CLI-аргументов
    if args.quality is not None and not (1 <= args.quality <= 100):
        parser.error("--quality должен быть в диапазоне 1-100")
    if args.max_long_side is not None and args.max_long_side <= 0:
        parser.error("--max-long-side должен быть положительным числом")
    if args.target_size is not None and args.target_size <= 0:
        parser.error("--target-size должен быть положительным числом")

    config = CompressionConfig()

    preset_map = {
        'max_quality': CompressionPreset.MAX_QUALITY,
        'balanced': CompressionPreset.BALANCED,
        'traffic_saving': CompressionPreset.TRAFFIC_SAVING,
    }
    config.apply_preset(preset_map[args.preset])

    if args.max_long_side is not None:
        config.max_long_side = args.max_long_side
    if args.quality is not None:
        config.jpeg_quality = args.quality
        config.webp_quality = args.quality
    if args.target_size is not None:
        config.target_max_size = args.target_size * 1024
    if args.no_exif:
        config.keep_exif = False
    if args.no_alpha:
        config.keep_alpha = False
    if args.workers:
        config.max_workers = args.workers

    source_paths: List[Path] = []
    for pattern in args.files:
        path = Path(pattern)
        if path.exists():
            if path.is_dir():
                if args.recursive:
                    for ext in ALL_IMAGE_FORMATS:
                        source_paths.extend(path.rglob(f'*{ext}'))
                else:
                    for ext in ALL_IMAGE_FORMATS:
                        source_paths.extend(path.glob(f'*{ext}'))
            else:
                source_paths.append(path)
        else:
            # Используем pathlib.Path.glob/rglob вместо glob.glob для производительности
            p = Path(pattern)
            if args.recursive:
                if '*' in p.name:
                    matched = [
                        f for f in p.parent.rglob(p.name)
                        if f.suffix.lower() in ALL_IMAGE_FORMATS
                    ]
                else:
                    matched = [
                        f for f in p.rglob('*')
                        if f.is_file() and f.suffix.lower() in ALL_IMAGE_FORMATS
                    ]
            else:
                matched = list(p.parent.glob(p.name)) if '*' in p.name else [p]
            if matched:
                source_paths.extend(matched)
            else:
                print(f"Файл не найден: {pattern}", file=sys.stderr)

    if not source_paths:
        print("Не найдено файлов для обработки.", file=sys.stderr)
        return 1

    source_paths = [p for p in source_paths if p.suffix.lower() in ALL_IMAGE_FORMATS]
    source_paths = list(set(source_paths))
    source_paths.sort()

    if not source_paths:
        print("Не найдено изображений для обработки.", file=sys.stderr)
        return 1

    print(f"Найдено файлов: {len(source_paths)}")

    compressor = ImageCompressor(config)

    if args.dry_run:
        print("\nПРОБНЫЙ ЗАПУСК (без сжатия)")
        print(f"Пресет: {args.preset}")
        print(f"Макс. длинная сторона: {config.max_long_side}px")
        print(f"Качество JPEG: {config.jpeg_quality}")
        print(f"Качество WebP: {config.webp_quality}")
        print(f"Целевой размер: {_format_size(config.target_max_size)}")
        print(f"Сохранять EXIF: {config.keep_exif}")
        print(f"Сохранять альфа: {config.keep_alpha}")
        print(f"Файлы для обработки:")
        for p in source_paths:
            size = p.stat().st_size
            print(f"  {p} ({_format_size(size)})")
        return 0

    def progress_callback(completed: int, total: int, result: CompressionResult):
        bar_width = 40
        fraction = completed / total
        filled = int(bar_width * fraction)
        bar = '█' * filled + '░' * (bar_width - filled)
        status = "OK" if not result.error else "ERR"
        sys.stdout.write(
            f"\r[{bar}] {completed}/{total} | "
            f"{result.source_path.name}: {status} | "
            f"{_format_size(result.original_size)} -> {_format_size(result.compressed_size)}"
        )
        sys.stdout.flush()
        if completed == total:
            print()

    try:
        if args.batch and len(source_paths) > 1:
            results = compressor.compress_batch(
                source_paths,
                output_dir=args.output_dir,
                output_ext=args.output_ext,
                progress_callback=progress_callback,
            )
        else:
            results = []
            total = len(source_paths)
            for i, source_path in enumerate(source_paths, 1):
                if args.output_dir:
                    out_path = Path(args.output_dir)
                else:
                    out_path = None

                try:
                    result = compressor.compress(
                        source_path,
                        output_path=out_path,
                        output_ext=args.output_ext,
                    )
                except Exception as e:
                    result = CompressionResult(
                        source_path=source_path,
                        output_path=source_path,
                        original_size=0,
                        compressed_size=0,
                        original_format=source_path.suffix.lower(),
                        output_format=args.output_ext or source_path.suffix.lower(),
                        original_dimensions=(0, 0),
                        compressed_dimensions=(0, 0),
                        compression_ratio=1.0,
                        was_resized=False,
                        was_converted=False,
                        exif_preserved=False,
                        processing_time=0.0,
                        error=str(e),
                    )

                results.append(result)
                progress_callback(i, total, result)

    except KeyboardInterrupt:
        print("\n\nПрервано пользователем.")
        return 130

    print()
    print(compressor.format_report(results, detailed=args.detailed))

    return 0 if not any(r.error for r in results) else 1


if __name__ == '__main__':
    sys.exit(cli_main())