FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY web/backend/pyproject.toml /app/pyproject.toml
COPY web/backend/cleair_backend /app/cleair_backend

RUN pip install --no-cache-dir .

EXPOSE 8000

CMD ["serve", "--host", "0.0.0.0", "--port", "8000"]
