FROM python:3.11-slim

WORKDIR /app

COPY services/gateway/pyproject.toml /app/pyproject.toml
COPY services/gateway/README.md /app/README.md
COPY services/gateway/src /app/src

RUN pip install --no-cache-dir .

EXPOSE 8000

CMD ["uvicorn", "gateway.main:app", "--app-dir", "src", "--host", "0.0.0.0", "--port", "8000"]
