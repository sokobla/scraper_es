# Use an official Python runtime as a parent image.
# Make sure this matches the Python version you are using for development.
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install system dependencies required for building psycopg2 from source
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers and their dependencies
RUN playwright install --with-deps

# Copy the rest of your application's code into the container
COPY . .

# Define the command to run your application
CMD ["python", "run_scrapper.py"]