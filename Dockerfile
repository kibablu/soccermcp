FROM python:3.11-slim

# 1. Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# 2. Copy dependency files
COPY pyproject.toml . 
# If you have requirements.txt instead, use: COPY requirements.txt .

# 3. Install dependencies 
# Added sse-starlette which is required for transport="sse"
RUN uv pip install --system fastmcp soccerdata pandas tabulate uvicorn sse-starlette

# 4. Copy source code
COPY . .

# Ensure the cache directory exists and is writable
ENV SOCCERDATA_DIR=/tmp/soccerdata

EXPOSE 8080

CMD ["python", "soccer_mcp.py"]
