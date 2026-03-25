# NOVA — Voice AI Email Assistant
# Docker build: docker build -t nova-assistant .
# Docker run:   docker run -p 5000:5000 -v $(pwd)/credentials.json:/app/credentials.json nova-assistant

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (needed for pyttsx3 and audio)
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (Docker cache optimization)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY app.py .

# Copy credentials if present (optional - can also mount at runtime)
COPY credentials.json* ./

# Expose port
EXPOSE 5000

# Environment variables
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Run the app
CMD ["python", "app.py"]