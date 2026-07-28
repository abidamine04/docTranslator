FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /srv
RUN groupadd --system app && useradd --system --gid app --uid 10001 --home-dir /nonexistent app
RUN apt-get update && apt-get install -y --no-install-recommends libmagic1 fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*
COPY apps/api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY apps/api/app ./app
COPY apps/api/alembic.ini ./alembic.ini
COPY apps/api/migrations ./migrations
RUN mkdir -p /data/documents && chown -R app:app /data/documents
USER app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
