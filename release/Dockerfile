# 使用ARG指令支持不同Python版本
ARG PYTHON_VERSION=3.10
FROM python:${PYTHON_VERSION}-slim

WORKDIR /app

# 复制发布包（而不是源代码）
COPY zr_daily_report_*.zip ./package.zip

# 安装unzip工具并解压
RUN apt-get update && \
    apt-get install -y unzip && \
    unzip package.zip && \
    rm package.zip && \
    apt-get remove -y unzip && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 设置环境变量以支持中文
ENV PYTHONIOENCODING=utf-8
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# 安装Windows兼容工具
RUN apt-get update && \
    apt-get install -y dos2unix && \
    find . -type f -name "*.bat" -exec dos2unix {} \; && \
    apt-get remove -y dos2unix && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 运行安装脚本
CMD ["bash", "-c", "chmod +x ./install.bat && ./install.bat"]