# ---------- Builder stage ----------
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build-time dependencies
COPY pyproject.toml requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# ---------- Runtime stage ----------
FROM python:3.11-slim AS runtime

WORKDIR /app

# Copy installed packages, binaries, and source from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app /app

EXPOSE 8000

# Run the FastAPI app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]