# Docker Build Design – Multi‑stage (Tag: `games:latest`)

## Overview
Create a lightweight production Docker image for the FastAPI game service using a multi‑stage build. The builder stage installs all Python dependencies, then the runtime stage copies only the necessary artifacts, resulting in a smaller final image.

## Dockerfile
```dockerfile
# ---------- Builder stage ----------
FROM python:3.11-slim AS builder
WORKDIR /app

# Install dependencies
COPY pyproject.toml requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# ---------- Runtime stage ----------
FROM python:3.11-slim AS runtime
WORKDIR /app

# Copy installed packages and source from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /app /app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Build Command
```bash
docker build -t games:latest .
```

## Benefits
- **Reduced image size** – only runtime dependencies remain.
- **Layer caching** – dependency installation is cached separately from source changes.
- **Simple workflow** – single Dockerfile, no Buildx required.

## Open Questions
- Any additional OS packages needed in the builder stage?
- Should the image be pushed to a registry after build?

*Design approved by user.*
