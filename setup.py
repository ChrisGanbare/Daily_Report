from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

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
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "zr-report=ZR_Daily_Report:main",
        ],
    },
    package_data={
        "": ["config/*", "template/*"],
    },
    include_package_data=True,
)