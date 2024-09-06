# Use the official Python image with version 3.12
FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any necessary dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 80:8000
# Create a volume for the log file
VOLUME ["/app/logs"]

# Command to run your application
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
