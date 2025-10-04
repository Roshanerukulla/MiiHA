
FROM python:3.11-slim

# Set working directory in container
WORKDIR /app

# Install build essentials (optional, for compiling dependencies)
RUN apt-get update && apt-get install -y build-essential

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
# Copy the entire project into container
COPY . /app


# Start Uvicorn with the app in app.main:app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]


# Set working directory in container
WORKDIR /app

RUN apt-get update && apt-get install -y build-essential

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# Copy the entire project into container
COPY . /app



# Start Uvicorn with the app in app.main:app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
