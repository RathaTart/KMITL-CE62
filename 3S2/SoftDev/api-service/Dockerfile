FROM astral/uv:debian-slim
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync
COPY . .
EXPOSE 8000
CMD ["uv", "run", "fastapi", "run", "app.py"]