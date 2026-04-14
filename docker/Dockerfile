FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install poetry
RUN pip install poetry
RUN poetry config virtualenvs.create false

# Copy dependency files first to leverage Docker cache
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-interaction --no-root

# Copy project files
COPY . .

# Expose Django port
EXPOSE 8000

# Default command (applies database migrations and runs server)
CMD ["sh", "-c", "python src/manage.py migrate && python src/manage.py runserver 0.0.0.0:8000"]
