FROM ghcr.io/railwayapp/nixpacks:ubuntu-1745885067

WORKDIR /app/

# Install basic tools and pip
RUN apt-get update && apt-get install -y python3 python3-pip python3-venv curl && rm -rf /var/lib/apt/lists/*

# Use existing pip (already installed via apt)

# Verify Python and pip are working
RUN python3 -V && python3 -m pip --version

# Copy application files
COPY . /app/.

# Install dependencies
RUN python3 -m pip install -r requirements.txt --break-system-packages

# Expose port
EXPOSE 8000

# Start FastAPI webhook
CMD ["python3", "-m", "uvicorn", "webhook_app:app", "--host", "0.0.0.0", "--port", "8000"]
