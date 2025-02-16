# Use the official Python slim image
FROM python:3.12-slim-bookworm

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    nodejs \
    npm \
    libmagic-dev \
    build-essential

# Download and install uv
ADD https://astral.sh/uv/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh

# Set the working directory
WORKDIR /app

# Copy application files
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Pillow for image processing
RUN pip install Pillow

RUN npm install -g prettier@3.4.2


# Install Node.js dependencies for Prettier and markdownlint
RUN npm install -g prettier@3.4.2 markdownlint-cli

# Ensure the installed binary is on the PATH
ENV PATH="/root/.local/bin:$PATH"

# Expose the FastAPI port
EXPOSE 8000

# Start the FastAPI app
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
