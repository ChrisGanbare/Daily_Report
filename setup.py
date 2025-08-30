from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()


setup(
    name="zr-daily-report",
    version="1.0.0",
    author="ZR Team",
    author_email="example@example.com",
    description="A Python application for generating daily inventory reports for cutting fluid equipment",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ChrisGanbare/Daily_Report",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Manufacturing",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "openpyxl==3.1.0",
        "mysql-connector-python==8.0.33",
        "cryptography==43.0.1",
    ],
    extras_require={
        "test": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "mock>=4.0.0",
        ],
        "dev": [
            "flake8>=5.0.0",
            "black>=22.0.0",
            "mypy>=0.971",
        ],
    },
    entry_points={
        "console_scripts": [
            "zr-report=zr_daily_report:main",
        ],
    },
    package_data={
        "": ["config/*", "template/*"],
    },
    include_package_data=True,
)