# Build stage
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Final stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies for psycopg2 and other packages if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 postgresql-client fonts-thai-tlwg \
    && rm -rf /var/lib/apt/lists/*

# Copy wheels from builder and install
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache /wheels/* && rm -rf /wheels

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DOCKER_ENV=1
ENV PORT=8000

# Create a non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Ensure user-installed scripts are on PATH
ENV PATH="/home/appuser/.local/bin:${PATH}"

EXPOSE 8000

# Healthcheck verifies the configured database, not only the web process.
HEALTHCHECK --interval=30s --timeout=30s --start-period=15s --retries=3 \
    CMD python healthcheck.py || exit 1

CMD ["python", "main.py"]
