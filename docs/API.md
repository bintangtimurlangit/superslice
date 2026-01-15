# SuperSlice API Documentation

## Base URL
```
http://localhost:8000
```

## Endpoints

### 1. Health Check
```
GET /
```

**Response:**
```json
{
  "service": "SuperSlice API",
  "status": "running",
  "version": "1.0.0"
}
```

### 2. Get Filament Types
```
GET /filament-types
```

**Response:**
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

### 3. Slice Model
```
POST /slice
```

**Content-Type:** `multipart/form-data`

**Parameters:**

| Parameter | Type | Required | Default | Range | Description |
|-----------|------|----------|---------|-------|-------------|
| file | file | Yes | - | - | 3D model file (STL or 3MF) |
| layer_height | float | No | 0.2 | 0.1 - 0.4 | Layer height in millimeters |
| infill_density | integer | No | 15 | 0 - 100 | Infill percentage |
| wall_count | integer | No | 2 | 1 - 10 | Number of perimeter walls |
| filament_type | string | No | "PLA" | - | Filament type (PLA, PETG, ABS, TPU, NYLON, ASA) |
| filament_density | float | No | null | - | Custom filament density in g/cm³ (overrides filament_type) |

**Request Example (curl):**
```bash
curl -X POST "http://localhost:8000/slice" \
  -F "file=@model.stl" \
  -F "layer_height=0.2" \
  -F "infill_density=15" \
  -F "wall_count=2" \
  -F "filament_type=PLA"
```

**Request Example (curl with custom density):**
```bash
curl -X POST "http://localhost:8000/slice" \
  -F "file=@model.stl" \
  -F "layer_height=0.2" \
  -F "infill_density=15" \
  -F "wall_count=2" \
  -F "filament_density=1.31"
```

**Request Example (Python):**
```python
import requests

url = "http://localhost:8000/slice"
files = {"file": open("model.stl", "rb")}
data = {
    "layer_height": 0.2,
    "infill_density": 15,
    "wall_count": 2,
    "filament_type": "PLA"
}

response = requests.post(url, files=files, data=data)
print(response.json())
```

**Request Example (JavaScript):**
```javascript
const formData = new FormData();
formData.append("file", fileInput.files[0]);
formData.append("layer_height", "0.2");
formData.append("infill_density", "15");
formData.append("wall_count", "2");
formData.append("filament_type", "PLA");

fetch("http://localhost:8000/slice", {
  method: "POST",
  body: formData
})
.then(response => response.json())
.then(data => console.log(data));
```

**Response (Success):**
```json
{
  "success": true,
  "print_time_minutes": 30.03,
  "print_time_formatted": "30m 2s",
  "filament_length_mm": 1990.73,
  "filament_volume_cm3": 4.79,
  "filament_weight_g": 6.27,
  "filament_type": "PLA",
  "layer_height": 0.2,
  "infill_density": 15,
  "wall_count": 2
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| success | boolean | Whether slicing succeeded |
| print_time_minutes | float | Estimated print time in minutes |
| print_time_formatted | string | Print time in human-readable format (e.g., "30m 2s") |
| filament_length_mm | float | Total filament length in millimeters |
| filament_volume_cm3 | float | Total filament volume in cubic centimeters |
| filament_weight_g | float | Total filament weight in grams |
| filament_type | string | Filament type used for calculation |
| layer_height | float | Layer height used for slicing |
| infill_density | integer | Infill percentage used for slicing |
| wall_count | integer | Number of walls used for slicing |

**Error Responses:**

**400 Bad Request:**
```json
{
  "detail": "Only STL and 3MF files are supported"
}
```

**408 Request Timeout:**
```json
{
  "detail": "Slicing timeout - model too complex"
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Slicing failed: [error message]"
}
```

## Interactive Documentation

Access the interactive API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
