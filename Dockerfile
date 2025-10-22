# Use a Python base image suitable for production
FROM python:3.9-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1  # Ensures Python output goes directly to container logs
ENV PORT=8080           # Application port

# Set the working directory inside the container
WORKDIR /app

# --- 1. Install Dependencies ---
# Copy requirements file first for Docker layer caching efficiency
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- 2. Copy Application Code and Artifacts ---
# CRITICAL: These COPY lines now include the ML model and the web app files
COPY app.py .
COPY feature.joblib .
COPY rfmodel_compressed_max.joblib .
COPY templates/ templates/ 

# --- 3. Expose Port ---
# Expose the port where Gunicorn will listen (matches the Kubernetes Service targetPort: 8080)
EXPOSE 8080

# --- 4. Define Production Startup Command ---
# CMD uses Gunicorn to run the Flask application ('app:app') on the specified port.
# This matches the targetPort: 8080 fix we applied to the Kubernetes Service.
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]