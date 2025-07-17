ARG BUILD_FROM
FROM $BUILD_FROM

# Install system dependencies
RUN apk add --no-cache \
    python3 \
    py3-pip \
    py3-numpy \
    py3-pillow \
    opencv-python3 \
    && rm -rf /var/cache/apk/*

# Install Python dependencies
COPY requirements.txt /tmp/
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

# Copy addon files
COPY rootfs/ /

# Set working directory
WORKDIR /opt/brokkoli_analysis

# Make run script executable
RUN chmod a+x /opt/brokkoli_analysis/run.sh

# Start addon
CMD ["/opt/brokkoli_analysis/run.sh"] 