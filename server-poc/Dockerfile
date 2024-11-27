FROM python:3.10-slim
# Configure Poetry
ENV POETRY_VERSION=1.5.1
ENV POETRY_HOME=/opt/poetry
ENV POETRY_VENV=/opt/poetry-venv
ENV POETRY_CACHE_DIR=/opt/.cache

# Install poetry separated from system interpreter
RUN python3 -m venv $POETRY_VENV \
    && $POETRY_VENV/bin/pip install -U pip setuptools \
    && $POETRY_VENV/bin/pip install poetry==${POETRY_VERSION}

# Add `poetry` to PATH
ENV PATH="${PATH}:${POETRY_VENV}/bin"

WORKDIR /app

# Copy the entire project first
COPY . ./server-poc/


# Then install server-poc dependencies
WORKDIR /app/server-poc
RUN poetry install

# Expose the port the app runs on
EXPOSE 80

# Command to run the application
CMD ["poetry", "run", "uvicorn", "server_poc.server:app", "--host", "0.0.0.0", "--port", "80"] 