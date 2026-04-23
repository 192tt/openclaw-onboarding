FROM python:3.11-slim

WORKDIR /app

# 安装依赖
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# 复制代码
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# 创建数据目录
RUN mkdir -p /app/data

EXPOSE 8000

WORKDIR /app/backend
CMD ["python", "main.py"]
