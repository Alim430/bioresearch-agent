from setuptools import setup, find_packages

setup(
    name="bioresearch-agent",
    version="0.1.0",
    description="An open-source, reproducible workflow framework for structured biomedical research",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Alimujiang Tudiyusufu",
    author_email="Alim_T@foxmail.com",
    url="https://github.com/Alim430/bioresearch-agent",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "bioresearch=bioresearch.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
    ],
    python_requires=">=3.9",
    install_requires=[
        "numpy>=1.21",
        "pandas>=1.3",
        "scipy>=1.7",
        "matplotlib>=3.4",
        "requests>=2.28",
        "pyyaml>=6.0",
    ],
    extras_require={
        "dev": ["pytest>=7.0", "black", "flake8", "mypy"],
        "llm": ["openai>=1.0", "anthropic>=0.8"],
    },
)
