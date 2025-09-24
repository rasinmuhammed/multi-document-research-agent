# Enhanced AI Research Agent - Production Docker Image
FROM python:3.11-slim

LABEL maintainer="AI Research Agent Team"
LABEL version="2.0"
LABEL description="Production-grade multi-document research agent"

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DEBIAN_FRONTEND=noninteractive

# Create application directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    git \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash --uid 1000 appuser

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data documents logs templates

# Set ownership to appuser
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Create sample environment file
RUN echo "# Enhanced AI Research Agent Configuration\n\
# Required: Get your API key from https://console.groq.com/\n\
GROQ_API_KEY=your_groq_api_key_here\n\
\n\
# Server configuration\n\
HOST=0.0.0.0\n\
PORT=5001\n\
DEBUG=False\n\
\n\
# Advanced settings\n\
MAX_TOKENS=4000\n\
TEMPERATURE=0.1\n\
CHUNK_SIZE=1000\n\
CHUNK_OVERLAP=200" > .env.example

# Expose port
EXPOSE 5001

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5001/api/status || exit 1

# Default command
CMD ["python", "run.py"]

# Multi-stage build for smaller production image (optional)
FROM python:3.11-slim as production

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install only runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy only necessary files from build stage
COPY --from=0 /app .
COPY --from=0 /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=0 /usr/local/bin /usr/local/bin

# Create appuser in production stage
RUN useradd --create-home --shell /bin/bash --uid 1000 appuser
RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 5001

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5001/api/status || exit 1

CMD ["python", "run.py"]