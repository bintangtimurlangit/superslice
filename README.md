# SuperSlice

[![Docker Build](https://github.com/bintangtimurlangit/superslice/actions/workflows/docker-build.yml/badge.svg)](https://github.com/bintangtimurlangit/superslice/actions/workflows/docker-build.yml)
[![GitHub release](https://img.shields.io/github/v/release/bintangtimurlangit/superslice)](https://github.com/bintangtimurlangit/superslice/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A REST API service for 3D print estimation using PrusaSlicer. Upload STL or 3MF files and receive detailed print statistics including time, filament usage, and material weight.

## Features

- RESTful API for 3D model slicing
- Support for STL and 3MF file formats
- Configurable slicing parameters (layer height, infill, walls)
- Predefined filament types with accurate density calculations (currently supports 6 common materials)
- Docker-based deployment for easy setup
- Health check endpoint for monitoring

Note: Currently only supports predefined filament types. Custom filament density support is available via the `filament_density` parameter.

## Filament Configuration

SuperSlice comes with predefined density values for common 3D printing filaments. These densities are used to calculate accurate material weight estimates.

### Supported Filament Types

| Filament Type | Density (g/cm³) | Description                                               |
| ------------- | --------------- | --------------------------------------------------------- |
| PLA           | 1.24            | Polylactic Acid - Most common, biodegradable              |
| PETG          | 1.27            | Polyethylene Terephthalate Glycol - Strong, flexible      |
| ABS           | 1.04            | Acrylonitrile Butadiene Styrene - Durable, heat resistant |
| TPU           | 1.21            | Thermoplastic Polyurethane - Flexible, rubber-like        |
| NYLON         | 1.14            | Polyamide - Strong, abrasion resistant                    |
| ASA           | 1.07            | Acrylonitrile Styrene Acrylate - UV resistant             |

### Using Custom Density

If your filament type is not listed or has a different density, you can override the density calculation:

```bash
curl -X POST http://localhost:8000/slice \
  -F "file=@model.stl" \
  -F "layer_height=0.2" \
  -F "infill_density=20" \
  -F "wall_count=3" \
  -F "filament_density=1.30"
```

To modify the predefined filament types, edit the `FILAMENT_DENSITIES` dictionary in `app/config.py`.

## Quick Start

### Prerequisites

- Docker
- Docker Compose (optional, for easier setup)

### Option 1: Use Pre-built Image (Recommended)

Pull and run the latest pre-built image from GitHub Container Registry:

```bash
docker run -d \
  --name superslice \
  -p 8000:8000 \
  ghcr.io/bintangtimurlangit/superslice:latest
```

Or use a specific version:

```bash
docker run -d \
  --name superslice \
  -p 8000:8000 \
  ghcr.io/bintangtimurlangit/superslice:1.0.0
```

Using docker-compose with pre-built image:

```yaml
version: "3.8"

services:
  superslice:
    image: ghcr.io/bintangtimurlangit/superslice:latest
    container_name: superslice
    ports:
      - "8000:8000"
    restart: unless-stopped
```

### Option 2: Build from Source

1. Clone the repository:

```bash
git clone <repository-url>
cd superslice
```

2. Build and run with Docker Compose:

```bash
docker-compose up -d
```

The API will be available at `http://localhost:8000`

### Verify Installation

Check the health endpoint:

```bash
curl http://localhost:8000/
```

Expected response:

```json
{
  "service": "SuperSlice API",
  "status": "running",
  "version": "1.0.0"
}
```

## API Usage

### Get Filament Types

Retrieve available filament types and their densities:

```bash
GET /filament-types
```

Response:

```json
{
  "filament_types": {
    "PLA": 1.24,
    "PETG": 1.27,
    "ABS": 1.04,
    "TPU": 1.21,
    "NYLON": 1.14,
    "ASA": 1.07
  }
}
```

### Slice a Model

Upload and slice a 3D model:

```bash
POST /slice
```

Parameters (form-data):

- `file` (required): 3D model file (STL or 3MF)
- `layer_height` (required): Layer height in mm (0.01 - 1.0)
- `infill_density` (required): Infill percentage (0 - 100)
- `wall_count` (required): Number of perimeter walls (1 - 20)
- `filament_type` (optional): Filament type (default: PLA)
- `filament_density` (optional): Custom density in g/cm³

Example using curl:

```bash
curl -X POST http://localhost:8000/slice \
  -F "file=@model.stl" \
  -F "layer_height=0.2" \
  -F "infill_density=20" \
  -F "wall_count=3" \
  -F "filament_type=PLA"
```

Response:

```json
{
  "success": true,
  "print_time_minutes": 45.5,
  "print_time_formatted": "45m 30s",
  "filament_length_mm": 1234.56,
  "filament_volume_cm3": 2.98,
  "filament_weight_g": 3.69,
  "filament_type": "PLA",
  "layer_height": 0.2,
  "infill_density": 20,
  "wall_count": 3
}
```

## Configuration

Environment variables can be configured in `.env` file or passed to Docker:

- `UPLOAD_DIR`: Directory for uploaded files (default: `/app/uploads`)
- `OUTPUT_DIR`: Directory for generated G-code (default: `/app/output`)
- `SLICE_TIMEOUT`: Maximum slicing time in seconds (default: `120`)
- `MAX_FILE_SIZE`: Maximum upload size in bytes (default: `104857600`)
- `CORS_ORIGINS`: Allowed CORS origins, comma-separated (default: `*`)

Example `.env` file:

```bash
SLICE_TIMEOUT=180
CORS_ORIGINS=https://example.com,https://app.example.com
```

## Development

### Project Structure

```
superslice/
├── app/
│   ├── main.py       # FastAPI application and routes
│   ├── config.py     # Configuration settings
│   ├── models.py     # Pydantic models
│   └── slicer.py     # PrusaSlicer integration
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

### Running Locally

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Run the application:

```bash
cd app
python main.py
```

Note: Local development requires PrusaSlicer to be installed and configured.

## API Documentation

Interactive API documentation is available at:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Error Handling

The API returns standard HTTP status codes:

- `200`: Success
- `400`: Invalid request parameters or unsupported file format
- `408`: Slicing timeout (model too complex)
- `500`: Internal server error

Error response format:

```json
{
  "detail": "Error message description"
}
```

## License

This project is provided as-is for 3D printing estimation purposes.
