# ZR Daily Report (Web Application)

**Version: 2.0.0**

ZR Daily Report is a modern, web-based application designed to generate daily and monthly consumption error reports for cutting fluid equipment. This version replaces the old GUI-based workflow with a streamlined, browser-based interface.

## ✨ Features

-   **Web-Based Interface**: Access the application from your browser. No complex GUI needed.
-   **Asynchronous Architecture**: Built with FastAPI and `aiomysql` for high performance.
-   **Dynamic Device Selection**: Easily search and select devices by customer name or device code.
-   **Multiple Report Types**: Generate different types of reports from a single, unified interface.
-   **High-Performance SQL**: Complex calculations are pushed down to the database layer for maximum efficiency.
-   **Centralized Configuration**: All settings are managed via Pydantic for type-safe configuration.

## 🚀 Getting Started

### Prerequisites

-   Python 3.8+
-   Access to the project's MySQL database.

### 1. Setup Virtual Environment

It is highly recommended to use a virtual environment to manage project dependencies.

```bash
# Create a virtual environment
python -m venv .venv

# Activate the virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
# source .venv/bin/activate
```

### 2. Install Dependencies

Install all necessary packages from `requirements.txt`. Using a domestic mirror source is recommended for faster downloads.

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 3. Configure the Application

The application uses environment variables (loaded from a `.env` file) and JSON files for configuration.

1.  **Create `.env` file**: Copy `.env.example` to `.env` in the project root and fill in your database credentials and other settings.
    ```bash
    cp .env.example .env
    # Then open .env and edit it
    ```
2.  **`config/query_config.json`**: This file contains SQL templates for various queries.
3.  **`config/error_summary_query.json`**: This file contains the high-performance SQL templates used for the daily consumption error report.

Ensure these files are correctly configured before running the application.

### 4. Run the Application

To start the web application, run the main entry point:

```bash
python src/main.py
```

After running the command, your default web browser will automatically open a new tab to `http://127.0.0.1:8000`, and you can start using the application. A separate console window will open to display server logs.

### 5. How to Stop

To stop the application, close the separate console window that opened for the server logs.

## 🛠️ Development & Testing

This project is equipped with a full suite of development tools to ensure code quality and consistency.

### Code Quality

The project uses `black`, `isort`, and `mypy`. You can run all checks using `tox`:

```bash
# Run all quality checks
tox -e quality
```

### Testing

The test suite is built with `pytest`. To run all tests:

```bash
# Run all tests
pytest
# Or via tox for isolated environment testing
tox
```

## 🏗️ Building a Distributable Package

A build script is provided to create a distributable package for the web application.

```bash
# Show help
python build_package.py help

# Create the distribution package (a .zip file in the root directory)
python build_package.py dist
```
