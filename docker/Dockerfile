# AegisTwin Production Dockerfile
# Multi-stage build for optimized image size
#
# @ai_prompt: Build with `docker build -t aegistwin:latest -f Dockerfile ..`
# @context_boundary: docker/Dockerfile
#
# AI-GENERATED 2026-01-07

# ============================================
# Stage 1: Builder
# ============================================
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy dependency files first for caching
COPY pyproject.toml ./

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# ============================================
# Stage 2: Production
# ============================================
FROM python:3.11-slim AS production

# Labels
LABEL org.opencontainers.image.title="AegisTwin"
LABEL org.opencontainers.image.description="Event-driven agent runtime + governance + deterministic replay"
LABEL org.opencontainers.image.version="0.1.0"
LABEL org.opencontainers.image.vendor="AegisTwin"

# Create non-root user
RUN groupadd -r aegistwin && useradd -r -g aegistwin aegistwin

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY aegistwin/ ./aegistwin/
COPY pyproject.toml ./

# Install the package
RUN pip install --no-cache-dir -e .

# Create directories for runtime data
RUN mkdir -p /app/runs /app/logs && \
    chown -R aegistwin:aegistwin /app

# Switch to non-root user
USER aegistwin

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV AEGISTWIN_RUNS_DIR=/app/runs
ENV AEGISTWIN_LOG_LEVEL=INFO

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run the application
CMD ["uvicorn", "aegistwin.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
