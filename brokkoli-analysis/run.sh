#!/usr/bin/with-contenv bashio

# ==============================================================================
# Brokkoli Analysis Addon
# Starts the image analysis service
# ==============================================================================

declare log_level

# Set log level
log_level=$(bashio::config 'log_level' 'info')
bashio::log.info "Starting Brokkoli Analysis Addon with log level: ${log_level}"

# Change to application directory
cd /opt/brokkoli_analysis

# Start the Python application
exec python3 main.py 