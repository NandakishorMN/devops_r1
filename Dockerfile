# Use a Python base image suitable for production
FROM python:3.9-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Set the working directory inside the container
WORKDIR /app

# --- 1. Install Dependencies ---
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- 2. Copy Application Code and Artifacts ---
# CRITICAL: These COPY lines now include the ML model and the web app files
COPY app.py .
COPY feature.joblib .
COPY rfmodel_compressed_max.joblib .
COPY templates/ templates/ 

# --- 3. Expose Port ---
EXPOSE 8080

# --- 4. Define Production Startup Command ---
# CMD uses Gunicorn to run the Flask application ('app:app') on the specified port.
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]