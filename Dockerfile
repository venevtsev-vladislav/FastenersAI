FROM ghcr.io/railwayapp/nixpacks:ubuntu-1745885067

WORKDIR /app/

# Install Python 3.11 and basic tools
RUN apt-get update && apt-get install -y python3.11 python3.11-venv python3.11-dev curl && rm -rf /var/lib/apt/lists/*

# Create symlink for python3
RUN ln -sf /usr/bin/python3.11 /usr/bin/python3

# Install pip using get-pip.py
RUN curl -sSfL https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py && \
    python3 /tmp/get-pip.py && \
    rm -f /tmp/get-pip.py

# Verify Python and pip are working
RUN python3 -V && python3 -m pip --version

# Copy application files
COPY . /app/.

# Upgrade pip and install dependencies
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install -r requirements.txt

# Cache Deno function
RUN deno cache supabase/functions/fastener-search/index.ts

# Expose port
EXPOSE 8000

# Start FastAPI webhook
CMD ["uvicorn", "webhook_app:app", "--host", "0.0.0.0", "--port", "8000"]
