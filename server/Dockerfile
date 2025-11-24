# Start from a slim Python base image
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
# Set working directory
WORKDIR /app

# Copy dependency files first for caching
COPY pyproject.toml uv.lock* ./

# Install dependencies (using uv)
RUN uv export > requirements.txt \
    && uv pip install --system --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

CMD ["python", "main.py"]
