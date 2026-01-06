"""Setup script for Document AI Agent package."""

from setuptools import setup, find_packages
from pathlib import Path

# Read the contents of README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

setup(
    name="document-reader",
    version="0.1.0",
    author="DocumentReader Team",
    author_email="",
    description="A specialized Document AI Agent for reading and interpreting difficult documents",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/derek-betz/DocumentReader",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Image Recognition",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.21.0",
        "Pillow>=9.0.0",
        "opencv-python>=4.5.0",
        "pytesseract>=0.3.10",
        "pdf2image>=1.16.0",
        "PyPDF2>=3.0.0",
        "PyYAML>=6.0",
        "python-dotenv>=0.19.0",
    ],
    extras_require={
        "paddleocr": [
            "paddleocr>=2.6.0",
            "paddlepaddle>=2.4.0",
        ],
        "vision": [
            "openai>=1.0.0",
            "anthropic>=0.7.0",
        ],
        "layout": [
            "layoutparser>=0.3.4",
            "torch>=1.13.0",
            "torchvision>=0.14.0",
        ],
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "mypy>=0.950",
        ],
        "docs": [
            "sphinx>=4.5.0",
            "sphinx-rtd-theme>=1.0.0",
        ],
        "all": [
            "paddleocr>=2.6.0",
            "paddlepaddle>=2.4.0",
            "openai>=1.0.0",
            "anthropic>=0.7.0",
            "layoutparser>=0.3.4",
            "torch>=1.13.0",
            "torchvision>=0.14.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "process-documents=scripts.process_documents:main",
            "process-engineering-plans=scripts.process_engineering_plans:main",
        ],
    },
    include_package_data=True,
    package_data={
        "document_reader": ["*.yaml", "*.json"],
    },
    zip_safe=False,
)
