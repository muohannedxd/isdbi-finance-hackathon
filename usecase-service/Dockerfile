FROM python:3.9-slim

WORKDIR /app

# Install build dependencies and clean up in the same layer to reduce image size
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy and install requirements separately to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

EXPOSE 5001

CMD ["python", "app.py"]
