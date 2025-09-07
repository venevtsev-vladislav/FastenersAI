FROM ghcr.io/railwayapp/nixpacks:ubuntu-1745885067

WORKDIR /app/

# Install Python and pip through Nix directly
RUN nix-env -iA nixpkgs.python311 nixpkgs.python311Packages.pip nixpkgs.python311Packages.setuptools && nix-collect-garbage -d

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
