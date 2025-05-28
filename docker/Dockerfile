# Coding AI Agent - Production Dockerfile
FROM python:3.9-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Docker CLI (for container management)
RUN curl -fsSL https://get.docker.com | sh

# Create application user
RUN useradd -m -s /bin/bash coder && \
    usermod -aG docker coder

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/

# Create necessary directories
RUN mkdir -p /tmp/coding-agent-workspaces && \
    chown -R coder:coder /tmp/coding-agent-workspaces && \
    chown -R coder:coder /app

# Switch to application user
USER coder

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

# Expose port
EXPOSE 8002

# Run the application
CMD ["python", "-m", "uvicorn", "src.coding_agent.main:app", "--host", "0.0.0.0", "--port", "8002"]