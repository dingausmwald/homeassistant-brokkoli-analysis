#!/usr/bin/with-contenv bashio

bashio::log.info "Starting Brokkoli Analysis Addon..."

# Wait for MQTT broker to be available
bashio::log.info "Waiting for MQTT broker..."
MQTT_HOST=$(bashio::config 'mqtt.host')
MQTT_PORT=$(bashio::config 'mqtt.port')

while ! nc -z "${MQTT_HOST}" "${MQTT_PORT}"; do
    bashio::log.info "MQTT broker not ready, waiting..."
    sleep 5
done

bashio::log.info "MQTT broker is ready"

# Start the main application
exec python3 /opt/brokkoli_analysis/main.py 