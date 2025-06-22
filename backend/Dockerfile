# 使用多阶段构建优化镜像大小

# ---- 开发/构建阶段 ----
FROM python:3.9-slim as builder

WORKDIR /app

# 安装诗歌 (Poetry) 或其他依赖管理工具 (如果使用)
# RUN pip install poetry
# COPY poetry.lock pyproject.toml ./
# RUN poetry config virtualenvs.create false && poetry install --no-dev --no-interaction --no-ansi

# 如果直接使用 requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY ./app /app/app

# ---- 生产阶段 ----
FROM python:3.9-slim as production

WORKDIR /app

# 从构建阶段复制已安装的依赖
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=builder /app/requirements.txt . # 复制 requirements.txt 供参考或后续操作

# 复制应用代码
# 注意：如果 builder 阶段已经复制了 app，这里可能需要调整
# 如果 builder 阶段只安装依赖，则在此处复制 app
COPY ./app /app/app
# COPY . . # 如果想复制 backend 目录下的所有内容 (包括 .env.example 等)

# 设置环境变量 (虽然通常在 docker-compose 中设置，但也可以在这里设置默认值)
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH=/app

# 暴露端口
EXPOSE 8000

# 运行应用
# 使用 gunicorn 作为生产环境的 WSGI 服务器
# CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-c", "app/gunicorn_conf.py", "app.main:app"]
# 开发或简单场景下可以直接用 uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
