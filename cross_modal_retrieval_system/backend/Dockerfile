FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir \
    numpy \
    pillow \
    torch \
    torchvision \
    fastapi \
    uvicorn \
    pydantic-settings \
    pymilvus \
    confluent-kafka \
    python-multipart \
    httpx

COPY src ./src
COPY .env.example ./.env

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
