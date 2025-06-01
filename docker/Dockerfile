# Dependency-only build for Coding AI Agent
FROM python:3.13-slim as dependencies

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH="/app/src"

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

# Copy and install Python dependencies ONLY
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create directory structure (source will be mounted as volume)
RUN mkdir -p /app/src && \
    mkdir -p /app/logs && \
    mkdir -p /tmp/coding-agent-workspaces && \
    chown -R coder:coder /tmp/coding-agent-workspaces && \
    chown -R coder:coder /app

# Runtime stage - no source code copying
FROM dependencies as runtime

# Switch to application user
USER coder

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

# Expose port
EXPOSE 8002

# Run the application (source code mounted as volume)
CMD ["python", "-m", "uvicorn", "coding_agent.main:app", "--host", "0.0.0.0", "--port", "8002"]