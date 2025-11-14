# backend/Dockerfile (fixed)

FROM python:3.11-slim

# avoid Python buffering (nice for logs)
ENV PYTHONUNBUFFERED=1

# Set working dir before copying files
WORKDIR /app

# Install OS packages we need (nmap + build deps for some wheels)
# run as root (default)
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      nmap \
      gcc \
      libpq-dev \
      build-essential \
 && rm -rf /var/lib/apt/lists/*

# Copy requirements and upgrade pip first to avoid stale pip issues
COPY requirements.txt requirements.txt

# Upgrade pip and install Python deps as root (so it can write into system site-packages)
RUN python -m pip install --upgrade pip setuptools wheel \
 && pip install --no-cache-dir -r requirements.txt

# Install any small tools not listed in requirements (optional)
RUN pip install --no-cache-dir sqlmap

# Copy app code
COPY . .

# Create a non-root user and ensure /app is owned by that user
# Use UID 1001 to match your previous choice
RUN useradd -m -u 1001 appuser || true \
 && chown -R appuser:appuser /app

# Switch to the non-root user for running the app
USER appuser

# Expose and run
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
