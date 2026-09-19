FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PORT=7860

# Create non-root user required by Hugging Face Spaces (UID 1000)
RUN useradd -m -u 1000 user

WORKDIR /home/user/app

# Install dependencies first (better layer caching)
COPY backend/requirements.txt ./requirements.txt
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy backend application code
COPY backend/ ./

# Ensure app files are owned by the non-root user
RUN chown -R user:user /home/user/app && \
    chmod +x start_prod.sh || true

USER user

EXPOSE 7860

# Entrypoint found in code: app/main.py defines `app` (app.main:app).
# Migrations run automatically on FastAPI startup via run_migrations(),
# so a plain uvicorn launch is production-ready on Spaces (port 7860 mandatory).
# Fallback equivalent: ["bash", "start_prod.sh"] (uses $PORT).
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]
