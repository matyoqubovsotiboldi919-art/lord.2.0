FROM python:3.11-slim

WORKDIR /app

# dependencies
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# backend
COPY backend /app

# 🔥 FRONTENDNI HAM COPY QILAMIZ
COPY frontend /app/frontend

EXPOSE 8000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]