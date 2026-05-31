FROM python:3.11-slim

WORKDIR /app

# Install ping for the /api/nomad/ping endpoint
RUN apt-get update && apt-get install -y iputils-ping && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose the API port
EXPOSE 2060

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "2060"]
