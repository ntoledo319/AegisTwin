"""
Setup script for CogniLink.
"""

from setuptools import setup, find_packages

setup(
    name="cognilink",
    version="1.0.0",
    description="Personal Digital Communication Analyzer",
    author="CogniLink Team",
    author_email="info@cognilink.example.com",
    packages=find_packages(),
    install_requires=[
        "networkx>=2.6.0",
        "pyyaml>=6.0",
        "matplotlib>=3.5.0",
        "numpy>=1.20.0",
        "pandas>=1.3.0",
        "jinja2>=3.0.0",
        "colorama>=0.4.4",
        "tabulate>=0.8.9",
        "tqdm>=4.62.3",
        "wordcloud>=1.8.1",
        "seaborn>=0.11.2",
        "openpyxl>=3.0.9",
    ],
    extras_require={
        "nlp": [
            "spacy>=3.0.0",
            "nltk>=3.6.0",
            "gensim>=4.0.0",
            "langdetect>=1.0.9",
            "sumy>=0.8.1",
        ],
        "viz": [
            "plotly>=5.0.0",
            "seaborn>=0.11.0",
            "wordcloud>=1.8.1",
        ],
        "web": [
            "flask>=2.0.0",
            "flask-cors>=3.0.10",
            "waitress>=2.0.0",
        ],
        "full": [
            "spacy>=3.0.0",
            "nltk>=3.6.0",
            "gensim>=4.0.0",
            "langdetect>=1.0.9",
            "sumy>=0.8.1",
            "plotly>=5.0.0",
            "seaborn>=0.11.0",
            "wordcloud>=1.8.1",
            "flask>=2.0.0",
            "flask-cors>=3.0.10",
            "waitress>=2.0.0",
        ],
        "dev": [
            "pytest>=6.0.0",
            "black>=21.5b2",
            "flake8>=3.9.0",
            "mypy>=0.812",
        ],
    },
    entry_points={
        "console_scripts": [
            "cognilink=cognilink.main:main",
        ],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Communications",
        "Topic :: Scientific/Engineering :: Information Analysis",
    ],
    include_package_data=True,
    package_data={
        "cognilink": [
            "config/*.yaml",
            "interface/templates/*",
        ],
    },
)