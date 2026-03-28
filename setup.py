from setuptools import setup, find_packages

setup(
    name="firefeed-rss-parser",
    version="1.0.0",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "feedparser>=6.0.0",
        "beautifulsoup4>=4.12.0",
        "lxml>=4.9.0",
        "httpx>=0.25.0",
        "aiolimiter>=1.1.0",
        "aiocache>=0.12.0",
        "python-dotenv>=1.0.0",
        "loguru>=0.7.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "pytest-mock>=3.10.0",
            "black>=23.0.0",
            "ruff>=0.1.0",
        ],
    },
)