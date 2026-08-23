FROM node:22-alpine AS frontend-builder

WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
ARG VITE_API_BASE_URL=/api/v1
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
RUN npm run build

FROM python:3.12-slim AS application

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    STATIC_FILES_DIR=/app/frontend

WORKDIR /app/backend
COPY backend/ ./
RUN pip install .

# Cache the open-source embedding model in the image so hosted cold starts do
# not depend on downloading it again.
RUN python -c "from fastembed import TextEmbedding; next(TextEmbedding(model_name='sentence-transformers/all-MiniLM-L6-v2').embed(['warmup']))"

COPY --from=frontend-builder /frontend/dist /app/frontend

EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
