# Brokkoli Analysis - Home Assistant Addon

Ein Home Assistant Addon für die Analyse von Bildern und Videostreams zur Pflanzenüberwachung. Bietet Funktionen wie NDVI-Berechnung, Grüne-Pixel-Zählung, Fisheye-Korrektur und mehr.

## Features

- 📁 **Ordner-Überwachung**: Automatische Verarbeitung neuer Bilder in konfigurierbaren Ordnern
- 🌱 **Grüne Pixel-Zählung**: Zählt grüne Pixel zur Pflanzengesundheit-Überwachung
- 🔍 **Quadranten-Analyse**: Aufteilen von Bildern in 4 Quadranten für detaillierte Analyse
- 📡 **MQTT Discovery**: Automatische Sensor-Erkennung in Home Assistant
- 🔄 **Echtzeit-Updates**: Konfigurierbare Update-Intervalle
- 🎯 **Erweiterbar**: Modulare Architektur für zusätzliche Prozessoren (NDVI, Fisheye, etc.)

## Installation

### Voraussetzungen

- Home Assistant OS oder Home Assistant Supervised
- MQTT Broker (z.B. Mosquitto Addon)

### Schritte

1. **Repository hinzufügen**:
   - Gehe zu **Supervisor** → **Add-on Store** → **⋮** → **Repositories**
   - Füge diese URL hinzu: `https://github.com/your-username/brokkoli-analysis-addon`

2. **Addon installieren**:
   - Suche nach "Brokkoli Analysis" im Add-on Store
   - Klicke auf **Install**

3. **Konfiguration anpassen** (siehe unten)

4. **Addon starten**:
   - Klicke auf **Start**
   - Optional: Aktiviere **Auto-Start**

## Konfiguration

### Beispiel-Konfiguration

```yaml
mqtt:
  host: core-mosquitto
  port: 1883
  username: ""
  password: ""
  discovery_prefix: homeassistant

sources:
  - name: "Camera Left"
    type: folder
    path: "/share/brokkoli/camera_left"
    update_interval: 30
  - name: "Camera Right"
    type: folder
    path: "/share/brokkoli/camera_right"
    update_interval: 60

processors:
  - name: "Green Pixels"
    type: green_pixels
    enabled: true
    quadrants: false
  - name: "Green Pixels Quadrants"
    type: green_pixels
    enabled: true
    quadrants: true

log_level: info
```

### Konfiguration-Optionen

#### MQTT

| Option | Typ | Standard | Beschreibung |
|--------|-----|----------|-------------|
| `host` | string | `core-mosquitto` | MQTT Broker Hostname |
| `port` | int | `1883` | MQTT Broker Port |
| `username` | string | `""` | MQTT Benutzername (optional) |
| `password` | string | `""` | MQTT Passwort (optional) |
| `discovery_prefix` | string | `homeassistant` | Discovery Prefix für HA |

#### Sources (Bildquellen)

| Option | Typ | Standard | Beschreibung |
|--------|-----|----------|-------------|
| `name` | string | - | Name der Quelle |
| `type` | string | - | Typ: `folder` oder `stream` |
| `path` | string | - | Pfad zum Ordner (bei `folder`) |
| `update_interval` | int | `30` | Update-Intervall in Sekunden |

#### Processors (Bildverarbeitung)

| Option | Typ | Standard | Beschreibung |
|--------|-----|----------|-------------|
| `name` | string | - | Name des Processors |
| `type` | string | - | Typ: `green_pixels`, `ndvi`, etc. |
| `enabled` | bool | `true` | Processor aktiviert |
| `quadrants` | bool | `false` | Quadranten-Analyse aktivieren |

#### Allgemein

| Option | Typ | Standard | Beschreibung |
|--------|-----|----------|-------------|
| `log_level` | string | `info` | Log-Level: `debug`, `info`, `warning`, `error` |

## Verwendung

### Ordner-Setup

1. Erstelle Ordner für deine Kamera-Bilder:
   ```bash
   mkdir -p /share/brokkoli/camera_left
   mkdir -p /share/brokkoli/camera_right
   ```

2. Stelle sicher, dass deine Kamera oder Scripts Bilder in diese Ordner speichern

### Sensoren in Home Assistant

Nach dem Start des Addons werden automatisch Sensoren in Home Assistant erstellt:

- **Ohne Quadranten**: `sensor.green_pixels_green_pixels`
- **Mit Quadranten**: 
  - `sensor.green_pixels_quadrants_top_left`
  - `sensor.green_pixels_quadrants_top_right`
  - `sensor.green_pixels_quadrants_bottom_left`
  - `sensor.green_pixels_quadrants_bottom_right`

### Dashboard-Integration

Die Sensoren können direkt in Home Assistant Dashboards verwendet werden:

```yaml
type: gauge
entity: sensor.green_pixels_green_pixels
min: 0
max: 100
name: Grüne Pixel %
unit: "%"
```

## Unterstützte Bildformate

- JPEG (.jpg, .jpeg)
- PNG (.png)
- BMP (.bmp)
- TIFF (.tiff, .tif)

## Troubleshooting

### Addon startet nicht

1. Überprüfe die Logs: **Supervisor** → **Brokkoli Analysis** → **Log**
2. Stelle sicher, dass der MQTT Broker läuft
3. Überprüfe die Konfiguration auf Syntax-Fehler

### Keine Sensoren in Home Assistant

1. Überprüfe MQTT-Verbindung im Addon-Log
2. Stelle sicher, dass MQTT Discovery aktiviert ist
3. Neustart des Addons versuchen

### Bilder werden nicht verarbeitet

1. Überprüfe Ordner-Berechtigungen
2. Stelle sicher, dass Bilder im unterstützten Format vorliegen
3. Überprüfe `update_interval` in der Konfiguration

## Entwicklung

### Architektur

```
brokkoli-analysis/
├── sources/          # Bildquellen (Ordner, Stream)
├── processors/       # Bildverarbeitung (Grüne Pixel, NDVI, etc.)
├── mqtt_client.py    # MQTT Discovery & Publishing
├── coordinator.py    # Orchestrierung
└── main.py          # Haupteinstiegspunkt
```

### Neue Processor hinzufügen

1. Erstelle eine neue Klasse in `processors/`
2. Erbe von `BaseProcessor`
3. Implementiere `process_image()` und `get_sensor_configs()`
4. Registriere in `coordinator.py`

### Neue Source hinzufügen

1. Erstelle eine neue Klasse in `sources/`
2. Erbe von `BaseSource`
3. Implementiere `get_latest_image()`, `has_new_image()`, `start()`, `stop()`
4. Registriere in `coordinator.py`

## Roadmap

- [ ] **Stream-Support**: UDP/RTSP Streams
- [ ] **NDVI-Processor**: Normalized Difference Vegetation Index
- [ ] **Fisheye-Korrektur**: Entzerrung von Fisheye-Objektiven
- [ ] **Bildrotation**: Automatische Bildausrichtung
- [ ] **LLM-Integration**: KI-basierte Krankheitserkennung
- [ ] **Web-Interface**: Konfiguration über Web-UI

## Support

- **Issues**: [GitHub Issues](https://github.com/your-username/brokkoli-analysis-addon/issues)
- **Diskussionen**: [Home Assistant Community](https://community.home-assistant.io/)

## Lizenz

MIT License - siehe [LICENSE](LICENSE) Datei.

## Changelog

### v1.0.0
- Initiale Version
- Grüne Pixel-Zählung
- Ordner-Überwachung
- MQTT Discovery
- Quadranten-Analyse 