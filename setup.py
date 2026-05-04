"""
Setup script для установки пакета и регистрации CLI-команды image-compress.
"""
from setuptools import setup, find_packages

setup(
    name="gkuop-image-compressor",
    version="1.0.0",
    description="Механизм сжатия изображений",
    packages=find_packages(include=['services', 'services.*']),
    python_requires=">=3.8",
    install_requires=[
        "Pillow>=9.0.0",
    ],
    extras_require={
        "heif": ["pillow-heif>=0.18.0"],
        "svg": ["cairosvg>=2.7.0"],
        "all": ["pillow-heif>=0.18.0", "cairosvg>=2.7.0"],
    },
    entry_points={
        "console_scripts": [
            "image-compress=services.image_compressor:cli_main",
        ],
    },
)
