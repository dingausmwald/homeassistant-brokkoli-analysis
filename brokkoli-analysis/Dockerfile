ARG BUILD_FROM
FROM $BUILD_FROM

# Install system dependencies
RUN apk add --no-cache \
    python3 \
    python3-dev \
    py3-pip \
    py3-numpy \
    py3-opencv \
    libglib-dev \
    libsm-dev \
    libxext-dev \
    libxrender-dev \
    libgomp \
    && rm -rf /var/cache/apk/*

# Set working directory
WORKDIR /opt/brokkoli_analysis

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application files
COPY rootfs/ /

# Make run script executable
RUN chmod +x /opt/brokkoli_analysis/run.sh

# Set the entrypoint
ENTRYPOINT ["/opt/brokkoli_analysis/run.sh"] 