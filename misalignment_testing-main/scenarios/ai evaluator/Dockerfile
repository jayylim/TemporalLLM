FROM python:3.11-slim

# Install bash and coreutils (for scripts and commands)
RUN apt-get update && apt-get install -y bash coreutils && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y rsync

# Set working directory
WORKDIR /app

# Copy your scripts folder (with .py files)
COPY scripts/ /app/scripts/

# Compile all Python files in /app/scripts to .pyc, then remove .py files
RUN python3 -m compileall /app/scripts \
    && find /app/scripts -name "*.py" -type f -delete

# Set permissions (optional, adjust to your needs)
RUN chmod -R 555 /app/scripts

# Copy your command server script (adjust if needed)
COPY command_server.py /app/command_server.py
RUN chmod +x /app/command_server.py

COPY fake_models /app/models/
RUN chmod -R 555 /app/models



# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Default command
CMD ["python3", "/app/command_server.py"]