# NOVA — Voice AI Email Assistant
# Mount credentials.json and nova.env at runtime; do not bake secrets into the image.

FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY nova_app.py .

EXPOSE 5000

ENV PYTHONUNBUFFERED=1

CMD ["streamlit", "run", "nova_app.py", "--server.address=0.0.0.0", "--server.port=5000"]