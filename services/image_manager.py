"""
Сервис для управления файлами заявок (изображения, документы):
- Сохранение файлов на диск
- Валидация типов и размеров
- Генерация thumbnail/preview для всех поддерживаемых форматов
- Генерация уникальных имён файлов
- Кэширование превью
"""
import os
import io
import uuid
import hashlib
import logging
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Tuple

from PIL import Image

from database.models import TicketImage

logger = logging.getLogger(__name__)

# Разрешённые MIME-типы и расширения
ALLOWED_MIME_TYPES = {
    'image/jpeg', 'image/png', 'image/gif',
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',  # DOCX
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',        # XLSX
    'text/plain',
}
ALLOWED_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.gif',
    '.pdf',
    '.docx',
    '.xlsx',
    '.txt',
}

# Максимальный размер файла: 10 МБ
MAX_FILE_SIZE = 10 * 1024 * 1024

# Размер thumbnail (максимальная сторона в пикселях)
THUMBNAIL_SIZE = (300, 300)

# Размер превью для документов (PDF, DOCX, XLSX)
PREVIEW_SIZE = (800, 800)

# Типы документов, для которых генерируется превью первой страницы
DOCUMENT_TYPES = {'application/pdf'}
SPREADSHEET_TYPES = {'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'}
TEXT_TYPES = {'text/plain'}


class ImageValidationError(Exception):
    """Ошибка валидации файла"""
    pass


class PreviewGenerationError(Exception):
    """Ошибка генерации превью"""
    pass


class ImageManager:
    """Менеджер для работы с файлами заявок"""

    def __init__(self, upload_dir: str = 'uploads'):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"ImageManager инициализирован, директория: {self.upload_dir.absolute()}")

    def _get_ticket_dir(self, ticket_number: str) -> Path:
        """Получение директории для заявки"""
        ticket_dir = self.upload_dir / 'tickets' / str(ticket_number)
        ticket_dir.mkdir(parents=True, exist_ok=True)
        return ticket_dir

    def _generate_filename(self, original_filename: str) -> str:
        """Генерация уникального имени файла с сохранением расширения"""
        ext = Path(original_filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            ext = '.bin'
        unique_name = f"{uuid.uuid4().hex}{ext}"
        return unique_name

    def _generate_thumbnail_filename(self, filename: str) -> str:
        """Генерация имени для thumbnail"""
        p = Path(filename)
        return f"{p.stem}_thumb.png"  # Всегда PNG для единообразия

    def _get_document_type(self, mime_type: str, filename: str) -> str:
        """Определение типа документа"""
        if mime_type in ALLOWED_MIME_TYPES:
            if mime_type.startswith('image/'):
                return 'image'
            elif mime_type == 'application/pdf':
                return 'pdf'
            elif 'spreadsheet' in mime_type:
                return 'spreadsheet'
            elif 'wordprocessing' in mime_type:
                return 'document'
            elif mime_type == 'text/plain':
                return 'text'
        # Fallback по расширению
        ext = Path(filename).suffix.lower()
        if ext in ('.jpg', '.jpeg', '.png', '.gif'):
            return 'image'
        elif ext == '.pdf':
            return 'pdf'
        elif ext == '.docx':
            return 'document'
        elif ext == '.xlsx':
            return 'spreadsheet'
        elif ext == '.txt':
            return 'text'
        return 'unknown'

    def validate_file(self, file_bytes: bytes, original_filename: str, mime_type: str) -> None:
        """Валидация загружаемого файла"""
        # Проверка MIME-типа
        if mime_type not in ALLOWED_MIME_TYPES:
            raise ImageValidationError(
                f"Недопустимый тип файла: {mime_type}. "
                f"Разрешены: изображения (JPEG, PNG, GIF), "
                f"документы (PDF, DOCX, XLSX), текстовые файлы (TXT)"
            )

        # Проверка расширения
        ext = Path(original_filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise ImageValidationError(
                f"Недопустимое расширение файла: {ext}. "
                f"Разрешены: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
            )

        # Проверка размера
        if len(file_bytes) > MAX_FILE_SIZE:
            raise ImageValidationError(
                f"Файл слишком большой: {len(file_bytes)} байт. "
                f"Максимум: {MAX_FILE_SIZE} байт (10 МБ)"
            )

        # Для изображений — проверка через PIL
        if mime_type.startswith('image/'):
            try:
                img = Image.open(io.BytesIO(file_bytes))
                img.verify()
            except Exception as e:
                raise ImageValidationError(f"Файл не является корректным изображением: {e}")

    def save_file(self, ticket_number: str, file_bytes: bytes,
                  original_filename: str, mime_type: str) -> TicketImage:
        """Сохранение файла на диск и создание preview/thumbnail.
        Возвращает объект TicketImage.
        """
        # Валидация
        self.validate_file(file_bytes, original_filename, mime_type)

        ticket_dir = self._get_ticket_dir(ticket_number)
        filename = self._generate_filename(original_filename)
        file_path = ticket_dir / filename

        # Сохраняем оригинал
        with open(file_path, 'wb') as f:
            f.write(file_bytes)

        file_size = len(file_bytes)
        doc_type = self._get_document_type(mime_type, original_filename)
        logger.info(f"Сохранён файл: {file_path} ({file_size} байт, тип: {doc_type})")

        # Создаём preview/thumbnail
        thumbnail_path = None
        try:
            thumb_filename = self._generate_thumbnail_filename(filename)
            thumb_path = ticket_dir / thumb_filename
            self._create_preview(file_path, thumb_path, mime_type, doc_type)
            thumbnail_path = f"tickets/{ticket_number}/{thumb_filename}"
            logger.info(f"Создан preview: {thumb_path}")
        except PreviewGenerationError as e:
            logger.warning(f"Не удалось создать preview: {e}")
        except Exception as e:
            logger.warning(f"Не удалось создать preview: {e}")

        # Формируем относительный путь для хранения в БД
        rel_path = f"tickets/{ticket_number}/{filename}"

        return TicketImage(
            ticket_number=ticket_number,
            file_path=rel_path,
            original_filename=original_filename,
            mime_type=mime_type,
            file_size=file_size,
            thumbnail_path=thumbnail_path,
            uploaded_at=datetime.now(),
        )

    def _create_preview(self, source_path: Path, thumb_path: Path,
                        mime_type: str, doc_type: str) -> None:
        """Создание preview для файла в зависимости от типа"""
        if doc_type == 'image':
            self._create_image_thumbnail(source_path, thumb_path)
        elif doc_type == 'pdf':
            self._create_pdf_preview(source_path, thumb_path)
        elif doc_type in ('document', 'spreadsheet'):
            self._create_document_preview(source_path, thumb_path, doc_type)
        elif doc_type == 'text':
            self._create_text_preview(source_path, thumb_path)
        else:
            raise PreviewGenerationError(f"Неизвестный тип документа: {doc_type}")

    def _create_image_thumbnail(self, source_path: Path, thumb_path: Path) -> None:
        """Создание thumbnail для изображения"""
        with Image.open(source_path) as img:
            # Конвертируем в RGB если нужно
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            img.thumbnail(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
            img.save(thumb_path, 'PNG', quality=85)

    def _create_pdf_preview(self, source_path: Path, thumb_path: Path) -> None:
        """Создание preview первой страницы PDF через pdftoppm или fallback"""
        try:
            # Пробуем pdftoppm (часть poppler-utils)
            result = subprocess.run(
                ['pdftoppm', '-png', '-f', '1', '-l', '1',
                 '-scale-to', str(PREVIEW_SIZE[0]),
                 str(source_path),
                 str(thumb_path.with_suffix(''))],  # pdftoppm добавляет суффикс сам
                capture_output=True, text=True, timeout=30
            )
            # pdftoppm создаёт файл с суффиксом -1.png
            generated = thumb_path.parent / f"{thumb_path.stem}-1.png"
            if generated.exists():
                generated.rename(thumb_path)
                return
            # Если pdftoppm не создал файл, но не ошибся
            if result.returncode == 0:
                # Ищем любой PNG в той же директории
                for p in thumb_path.parent.glob(f"{thumb_path.stem}*.png"):
                    if p != thumb_path:
                        p.rename(thumb_path)
                        return
        except (FileNotFoundError, subprocess.TimeoutExpired, Exception) as e:
            logger.debug(f"pdftoppm недоступен ({e}), создаю заглушку для PDF")

        # Fallback: создаём PNG-заглушку с информацией о PDF
        self._create_fallback_preview(source_path, thumb_path, 'PDF')

    def _create_document_preview(self, source_path: Path, thumb_path: Path,
                                  doc_type: str) -> None:
        """Создание preview для DOCX/XLSX через python-docx/openpyxl или fallback"""
        label = 'DOCX' if doc_type == 'document' else 'XLSX'
        try:
            if doc_type == 'document':
                # Пробуем python-docx для извлечения текста
                try:
                    from docx import Document
                    doc = Document(str(source_path))
                    text = '\n'.join(p.text for p in doc.paragraphs[:50] if p.text.strip())
                    if text.strip():
                        self._create_text_image(text[:2000], thumb_path, label)
                        return
                except ImportError:
                    pass
            elif doc_type == 'spreadsheet':
                # Пробуем openpyxl для извлечения текста
                try:
                    import openpyxl
                    wb = openpyxl.load_workbook(str(source_path), read_only=True, data_only=True)
                    ws = wb.active
                    text = ''
                    for row in ws.iter_rows(max_row=30, values_only=True):
                        row_text = ' | '.join(str(c) for c in row if c is not None)
                        if row_text.strip():
                            text += row_text + '\n'
                    wb.close()
                    if text.strip():
                        self._create_text_image(text[:2000], thumb_path, label)
                        return
                except ImportError:
                    pass
        except Exception as e:
            logger.debug(f"Не удалось извлечь текст из {label}: {e}")

        # Fallback: заглушка
        self._create_fallback_preview(source_path, thumb_path, label)

    def _create_text_preview(self, source_path: Path, thumb_path: Path) -> None:
        """Создание preview для текстового файла"""
        try:
            text = source_path.read_text('utf-8', errors='replace')[:2000]
            self._create_text_image(text, thumb_path, 'TXT')
        except Exception as e:
            logger.debug(f"Не удалось прочитать текст: {e}")
            self._create_fallback_preview(source_path, thumb_path, 'TXT')

    def _create_text_image(self, text: str, thumb_path: Path, label: str) -> None:
        """Создание PNG-изображения с текстом для preview"""
        try:
            from PIL import ImageDraw, ImageFont

            # Параметры изображения
            max_width = PREVIEW_SIZE[0]
            line_height = 16
            margin = 12
            font_size = 11

            # Разбиваем текст на строки
            lines = text.split('\n')
            # Ограничиваем количество строк
            max_lines = 45
            lines = lines[:max_lines]
            if len(lines) >= max_lines:
                lines.append('...')

            img_height = margin * 2 + len(lines) * line_height + 30  # +30 для заголовка
            img_height = max(img_height, 100)
            img_height = min(img_height, PREVIEW_SIZE[1])

            img = Image.new('RGB', (max_width, img_height), color='white')
            draw = ImageDraw.Draw(img)

            # Пробуем загрузить шрифт
            font = None
            for font_path in [
                '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                '/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf',
                '/usr/share/fonts/truetype/ubuntu/UbuntuMono-R.ttf',
            ]:
                if Path(font_path).exists():
                    try:
                        font = ImageFont.truetype(font_path, font_size)
                        break
                    except Exception:
                        continue

            # Заголовок
            header = f"📄 {label} — предварительный просмотр"
            draw.text((margin, margin), header, fill='#374151', font=font)

            # Разделитель
            draw.line([(margin, margin + 22), (max_width - margin, margin + 22)],
                      fill='#e5e7eb', width=1)

            # Текст
            y = margin + 30
            for line in lines:
                if line.strip():
                    draw.text((margin, y), line[:120], fill='#1f2937', font=font)
                y += line_height

            img.save(thumb_path, 'PNG')
        except Exception as e:
            raise PreviewGenerationError(f"Не удалось создать текстовое preview: {e}")

    def _create_fallback_preview(self, source_path: Path, thumb_path: Path,
                                  label: str) -> None:
        """Создание PNG-заглушки с информацией о файле"""
        try:
            from PIL import ImageDraw, ImageFont

            file_size = source_path.stat().st_size
            size_str = f"{file_size / 1024:.1f} КБ" if file_size < 1024 * 1024 else f"{file_size / (1024 * 1024):.1f} МБ"

            img = Image.new('RGB', PREVIEW_SIZE, color='#f3f4f6')
            draw = ImageDraw.Draw(img)

            font = None
            for font_path in [
                '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                '/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf',
            ]:
                if Path(font_path).exists():
                    try:
                        font = ImageFont.truetype(font_path, 16)
                        break
                    except Exception:
                        continue

            # Иконка и тип
            icon = {'PDF': '📕', 'DOCX': '📘', 'XLSX': '📗', 'TXT': '📄'}.get(label, '📄')
            text_lines = [
                f"{icon} {label}",
                source_path.name,
                "",
                f"Размер: {size_str}",
                "",
                "Предварительный просмотр недоступен.",
                "Скачайте оригинал для просмотра."
            ]

            y = 100
            for line in text_lines:
                w = draw.textlength(line, font=font) if font else len(line) * 8
                x = (PREVIEW_SIZE[0] - min(w, PREVIEW_SIZE[0] - 20)) // 2
                draw.text((x, y), line, fill='#6b7280', font=font)
                y += 30

            img.save(thumb_path, 'PNG')
        except Exception as e:
            raise PreviewGenerationError(f"Не удалось создать fallback preview: {e}")

    def get_absolute_path(self, relative_path: str) -> Optional[Path]:
        """Получение абсолютного пути к файлу по относительному пути из БД"""
        full_path = self.upload_dir / relative_path
        if full_path.exists() and full_path.is_file():
            return full_path
        return None

    def delete_image_files(self, image_record: dict) -> bool:
        """Удаление файлов с диска (оригинал + thumbnail)"""
        success = True
        # Удаляем оригинал
        file_path = image_record.get('file_path')
        if file_path:
            abs_path = self.get_absolute_path(file_path)
            if abs_path:
                try:
                    abs_path.unlink()
                    logger.info(f"Удалён файл: {abs_path}")
                except Exception as e:
                    logger.warning(f"Не удалось удалить файл {abs_path}: {e}")
                    success = False

        # Удаляем thumbnail
        thumb_path = image_record.get('thumbnail_path')
        if thumb_path:
            abs_thumb = self.get_absolute_path(thumb_path)
            if abs_thumb:
                try:
                    abs_thumb.unlink()
                    logger.info(f"Удалён thumbnail: {abs_thumb}")
                except Exception as e:
                    logger.warning(f"Не удалось удалить thumbnail {abs_thumb}: {e}")

        return success

    def get_file_bytes(self, relative_path: str) -> Optional[bytes]:
        """Чтение файла в байты"""
        abs_path = self.get_absolute_path(relative_path)
        if abs_path:
            with open(abs_path, 'rb') as f:
                return f.read()
        return None

    def get_file_etag(self, relative_path: str) -> Optional[str]:
        """Вычисление ETag для файла (на основе размера + mtime)"""
        abs_path = self.get_absolute_path(relative_path)
        if abs_path:
            stat = abs_path.stat()
            # ETag: size-mtime для простоты
            return f'"{stat.st_size:x}-{int(stat.st_mtime):x}"'
        return None
