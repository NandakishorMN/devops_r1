# Use a Python base image suitable for production
FROM python:3.9-slim

# Set environment variables (Fixed: using key=value format)
ENV PORT=8080
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

# Set the working directory inside the container
WORKDIR /app

# 1. Install necessary dependencies
# The COPY requirements.txt . copies the file from your local machine to the container
COPY requirements.txt .
# RUN pip install executes the installation
RUN pip install --no-cache-dir -r requirements.txt

# 2. Copy the application code and model files
# CRITICAL: These COPY lines must match the names of your files!
COPY app.py .
COPY feature.joblib .
COPY rfmodel_compressed_max.joblib .
COPY templates/ templates/ 

# 3. Expose the port (Kubernetes will use this to route traffic)
EXPOSE ${PORT}

# 4. Define the command to start the production web server (Gunicorn)
# Gunicorn serves your Flask app ('app:app') on the specified port.
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]