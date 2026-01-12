FROM python:3.10

WORKDIR /backend

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /uvx /bin/

# Copy dependency files
COPY ./pyproject.toml ./uv.lock /backend/

# Create venv in container and install dependencies
RUN uv venv /backend/.venv && \
    uv sync --frozen

# Copy application code
COPY ./alembic.ini /backend/
COPY ./src /backend/src
COPY ./alembic /backend/alembic

# Set Python path
ENV PYTHONPATH=/backend
ENV PATH="/backend/.venv/bin:$PATH"

# Expose port
EXPOSE 8000

# Run uvicorn from venv
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]