# Dockerfile
FROM python:3.13.6-slim

WORKDIR /app

# Install system deps
RUN apt-get update \
    && apt-get install -y build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . .

# Install dependencies including dev
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -e ".[dev]"

# Copy entrypoint
RUN chmod +x /app/entrypoint.sh

# Run the app
CMD ["./entrypoint.sh"]
