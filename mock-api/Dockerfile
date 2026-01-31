# Mock API Dockerfile
FROM python:3.13-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt* ./

# Install dependencies if requirements file exists
RUN pip install --no-cache-dir fastapi uvicorn pydantic python-dotenv

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8080/health')"

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
