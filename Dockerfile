FROM python:3.11-slim

# Do not create .pyc cache files inside the container
ENV PYTHONDONTWRITEBYTECODE=1

# Print Python logs immediately in Docker terminal
ENV PYTHONUNBUFFERED=1

# Set project folder inside the container
WORKDIR /app

# Install Linux packages required for OpenCV and MySQL client support
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libgl1 \
    default-mysql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependency list into the container
COPY requirements.txt .

# Install Python libraries from requirements.txt
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch==2.3.1+cpu torchvision==0.18.1+cpu

RUN pip install --no-cache-dir -r requirements.txt

# Copy project source code into the container
COPY . .

# Run the current ML + AWS + Telegram pipeline
CMD ["python", "video_pipeline/ml/inference/run_pipeline_on_videos.py"]
