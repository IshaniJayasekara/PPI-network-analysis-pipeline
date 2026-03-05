FROM python:3.9-slim

# Install system dependencies (procps is needed for Nextflow monitoring)
RUN apt-get update && apt-get install -y procps && rm -rf /var/lib/apt/lists/*

# Install Python libraries
RUN pip install --no-cache-dir \
    networkx \
    pandas \
    openpyxl \
    gprofiler-official \
    scipy \
    numpy \
    psutil

# Set working directory
WORKDIR /app
