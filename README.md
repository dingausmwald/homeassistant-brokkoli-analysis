# Brokkoli Analysis - Home Assistant Addon

Ein Home Assistant Addon für die Analyse von Bildern und Videostreams zur Pflanzenüberwachung mit NDVI, Grünpixel-Zählung und mehr.

## Features

- **Bildquellen**: Ordnerüberwachung für neue Bilder, Stream-Support geplant
- **Bildverarbeitung**: Grünpixel-Zählung, NDVI-Berechnung (geplant), Fisheye-Korrektur (geplant)
- **Quadranten-Analyse**: Aufteilen der Bilder in 4 Bereiche für detaillierte Analyse
- **MQTT Integration**: Automatische Sensor-Erkennung in Home Assistant über MQTT Discovery
- **Mehrere Pipelines**: Unterstützung für mehrere Kameras/Quellen parallel

## Installation

1. Füge dieses Repository zu deinen Home Assistant Addon-Repositories hinzu
2. Installiere das "Brokkoli Analysis" Addon
3. Konfiguriere das Addon über die UI
4. Starte das Addon

## Konfiguration

### MQTT Einstellungen
```yaml
mqtt:
  host: core-mosquitto
  port: 1883
  username: ""
  password: ""
  discovery_prefix: homeassistant
```

### Bildquellen
```yaml
sources:
  - name: "Camera Left"
    type: folder
    path: "/share/brokkoli/camera_left"
    update_interval: 30
  - name: "Camera Right"
    type: folder
    path: "/share/brokkoli/camera_right"
    update_interval: 30
```

### Bildverarbeitung
```yaml
processors:
  - name: "Green Pixels"
    type: green_pixels
    enabled: true
    quadrants: false
  - name: "NDVI"
    type: ndvi
    enabled: false
    quadrants: false
```

## Unterstützte Bildformate

- JPG/JPEG
- PNG
- BMP
- TIFF/TIF

## Sensoren in Home Assistant

Das Addon erstellt automatisch Sensoren in Home Assistant:

- `sensor.brokkoli_analysis_camera_left_green_pixels` - Anzahl grüner Pixel
- `sensor.brokkoli_analysis_camera_left_green_percentage` - Prozentsatz grüner Pixel

Bei aktivierten Quadranten zusätzlich:
- `sensor.brokkoli_analysis_camera_left_top_left_green_pixels`
- `sensor.brokkoli_analysis_camera_left_top_left_green_percentage`
- ... (für alle 4 Quadranten)

## Ordnerstruktur

```
/share/brokkoli/
├── camera_left/
│   ├── image_001.jpg
│   ├── image_002.jpg
│   └── ...
└── camera_right/
    ├── image_001.jpg
    ├── image_002.jpg
    └── ...
```

## Entwicklung

### Neue Bildquellen hinzufügen

1. Erstelle eine neue Klasse die von `BaseSource` erbt
2. Implementiere die abstrakten Methoden
3. Registriere die Quelle in `coordinator.py`

### Neue Bildverarbeitungsmodule hinzufügen

1. Erstelle eine neue Klasse die von `BaseProcessor` erbt
2. Implementiere die `process()` und `get_sensor_configs()` Methoden
3. Registriere den Processor in `coordinator.py`

## Geplante Features

- **Stream-Unterstützung**: UDP/RTSP Streams
- **NDVI-Berechnung**: Normalized Difference Vegetation Index
- **Fisheye-Korrektur**: Korrektur von Fisheye-Objektiven
- **Bildrotation**: Automatische Bildausrichtung
- **LLM-Integration**: KI-basierte Krankheitserkennung

## Lizenz

MIT License

## Support

Bei Problemen erstelle ein Issue im GitHub Repository. 