# 使用Python 3.10作为基础镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 复制项目文件
COPY . .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 创建非root用户
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# 设置环境变量
ENV PYTHONPATH=/app

# 暴露端口（如果需要web服务）
# EXPOSE 8000

# 定义启动命令
CMD ["python", "ZR_Daily_Report.py"]