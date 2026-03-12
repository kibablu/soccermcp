FROM python:3.11-slim

# 1. Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# 2. Copy ONLY the dependency files first
# This layer is cached unless pyproject.toml or requirements.txt changes
COPY pyproject.toml . 
# OR: COPY requirements.txt .

# 3. Install dependencies
# Because the source code isn't here yet, this layer stays cached!
RUN uv pip install --system fastmcp soccerdata pandas tabulate uvicorn

# 4. NOW copy the rest of your source code
# Since this is the last step, code changes won't trigger a re-install
COPY . .

EXPOSE 8080

CMD ["python", "soccer_server.py"]
