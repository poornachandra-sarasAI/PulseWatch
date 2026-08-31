# ── Backend image for PulseWatch API and scheduler ──────────────────────────
FROM python:3.11-slim AS base

WORKDIR /app

# Install Python dependencies first so this layer is cached between code changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend source.
COPY backend/ backend/

# The app package lives inside backend/, so tell Python where to find it.
ENV PYTHONPATH=/app/backend

# Default command runs the API server.
# Override with the scheduler command in docker-compose when needed:
#   python backend/scripts/run_scheduler.py --poll-interval 5
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
