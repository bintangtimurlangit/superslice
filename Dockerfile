# SuperSlice - All-in-one container with FastAPI + PrusaSlicer
FROM mikeah/prusaslicer-novnc:latest

# Install Python and dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application code
COPY ./app /app

# Create directories
RUN mkdir -p /app/uploads /app/output

# Expose port
EXPOSE 8000

# Override the base image's entrypoint
ENTRYPOINT []

# Run FastAPI with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
