# Start from a slim Python base image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install curl so we can get uv
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && curl -LsSf https://astral.sh/uv/install.sh | sh \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Add uv to PATH (uv installs in ~/.local/bin)
ENV PATH="/root/.local/bin:$PATH"

# Copy dependency file(s) first for caching
COPY pyproject.toml uv.lock* ./

# Install dependencies (using uv)
RUN uv export > requirements.txt \
    && uv pip install --system --no-cache-dir -r requirements.txt


# Copy application code
COPY . .

# Expose port if your app serves HTTP (change if needed)
# EXPOSE 8000

# Run your app (adjust command if needed)
CMD ["python", "main.py"]
