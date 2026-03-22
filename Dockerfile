# Stage 1: Build frontend
FROM node:20-slim AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Python runtime
FROM python:3.12-slim
WORKDIR /app

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/src/ ./src/

# Copy built frontend
COPY --from=frontend /app/frontend/dist ./static

ENV PYTHONPATH=/app/src

EXPOSE 8031

CMD ["uvicorn", "predictor.main:app", "--host", "0.0.0.0", "--port", "8031"]
