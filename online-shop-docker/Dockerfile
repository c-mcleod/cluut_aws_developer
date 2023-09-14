# Dockerfile
FROM python:3.7-slim

# Set working directory in the container
WORKDIR /app

# Copy the requirements.txt file to the container
COPY dash-container/requirements.txt .

# Install the required modules from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install gunicorn
RUN pip install gunicorn

# Copy all other files from the dash-container folder to the container
COPY dash-container/ .

# Expose the port on which the app will run (change the port number if needed)
EXPOSE 8080

# Run the gunicorn command to start the app
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:server"]      