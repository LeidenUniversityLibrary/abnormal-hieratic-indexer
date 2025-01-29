FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Clone the repository
RUN git clone https://github.com/LeidenUniversityLibrary/abnormal-hieratic-indexer.git /app

# Install dependencies based on pyproject.toml
RUN pip install --upgrade pip && pip install build
RUN python -m build
RUN pip install dist/*.whl  # or dist/*.tar.gz if it generates a source distribution

