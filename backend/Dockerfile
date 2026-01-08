FROM python:3.10


WORKDIR /backend


# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /uvx /bin/


# Place executables in the environment at the front of the path
ENV PATH="/backend/.venv/bin:$PATH"


# Compile bytecode
ENV UV_COMPILE_BYTECODE=1


# uv Cache
ENV UV_LINK_MODE=copy


# Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project


ENV PYTHONPATH=/backend


# Copy the project into the image
COPY ./pyproject.toml ./uv.lock ./alembic.ini /backend/


COPY ./src /backend/src


# Sync the project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

# Expose the port Uvicorn will run on
EXPOSE 8000

# Command to run the application with Uvicorn
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]