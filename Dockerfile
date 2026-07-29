# Use official Python image.
FROM python:3.11-slim

WORKDIR /app

# Install dependencies.
COPY pyproject.toml requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code.
COPY . .

EXPOSE 8000

# Run the FastAPI app.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
