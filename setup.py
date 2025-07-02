"""
Setup script for GranolaMCP.

A Python library for interfacing with Granola.ai meeting data using 100% native Python.
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return ""

# Read version from __init__.py
def get_version():
    version_file = os.path.join(os.path.dirname(__file__), 'granola_mcp', '__init__.py')
    with open(version_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('__version__'):
                return line.split('=')[1].strip().strip('"').strip("'")
    return "0.1.0"

setup(
    name="granola-mcp",
    version=get_version(),
    author="GranolaMCP Team",
    author_email="",
    description="A Python library for interfacing with Granola.ai meeting data",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/pedramamini/GranolaMCP",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Communications",
        "Topic :: Office/Business",
    ],
    python_requires=">=3.12",
    install_requires=[
        # No external dependencies - using only Python standard library
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "granola=granola_mcp.cli.main:main",
            "granola-mcp=granola_mcp.cli.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "granola_mcp": ["*.md", "*.txt"],
    },
    keywords=[
        "granola",
        "meetings",
        "transcription",
        "ai",
        "mcp",
        "model-context-protocol",
    ],
    project_urls={
        "Bug Reports": "https://github.com/pedramamini/GranolaMCP/issues",
        "Source": "https://github.com/pedramamini/GranolaMCP",
        "Documentation": "https://github.com/pedramamini/GranolaMCP/blob/main/README.md",
    },
)
