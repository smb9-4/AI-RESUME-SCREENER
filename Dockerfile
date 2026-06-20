# Use a lightweight official Python image
FROM python:3.10-slim

# Install socat to handle the database rerouting safely
RUN apt-get update && apt-get install -y socat && rm -rf /var/lib/apt/lists/*

# Set the directory inside the container
WORKDIR /app

# Copy all project files into the container
COPY . /app

# Install all Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Open the port Hugging Face requires
EXPOSE 7860

# Secret weapon: Start the database forwarder in the background, then launch Flask via Gunicorn
CMD socat TCP-LISTEN:27017,fork,reuseaddr TCP:cluster0.qz9rlw2.mongodb.net:27017 & \
    gunicorn -b 0.0.0.0:7860 app:app