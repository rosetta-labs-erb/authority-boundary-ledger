"""
Authority Boundary Ledger Setup
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="authority-boundary-ledger",
    version="0.1.0",
    author="Cameron Semple",
    author_email="cameronsemple@gmail.com",
    description="A governance primitive for persistent authority constraints in LLM systems",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/rosetta-labs-erb/authority-boundary-ledger",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "anthropic>=0.39.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
        ],
    },
)
