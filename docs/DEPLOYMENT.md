# Deployment Guide

This guide covers deploying SuperSlice in various environments.

## GitHub Container Registry Setup

The project is configured to automatically build and push Docker images to GitHub Container Registry (GHCR) when you push to the main branch or create a release tag.

### First-Time Setup

1. Push your code to GitHub:

```bash
git remote add origin https://github.com/bintangtimurlangit/superslice.git
git branch -M main
git push -u origin main
```

2. The GitHub Actions workflow will automatically build the Docker image

3. The image will be available at: `ghcr.io/bintangtimurlangit/superslice:latest`

### Creating a Release

To create a versioned release:

```bash
# Create and push a tag
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

This will trigger the workflow to build and push images with tags:

- `ghcr.io/bintangtimurlangit/superslice:1.0.0`
- `ghcr.io/bintangtimurlangit/superslice:1.0`
- `ghcr.io/bintangtimurlangit/superslice:1`
- `ghcr.io/bintangtimurlangit/superslice:latest`

### Making Images Public

By default, GHCR images are private. To make them public:

1. Go to https://github.com/bintangtimurlangit?tab=packages
2. Find the `superslice` package
3. Click on it
4. Go to "Package settings"
5. Scroll down to "Danger Zone"
6. Click "Change visibility" → "Public"

## Deployment Options

### Local Development

```bash
docker-compose up -d
```

### Production Server

1. Pull the image:

```bash
docker pull ghcr.io/bintangtimurlangit/superslice:latest
```

2. Run with environment variables:

```bash
docker run -d \
  --name superslice \
  -p 8000:8000 \
  -e SLICE_TIMEOUT=180 \
  -e CORS_ORIGINS=https://yourdomain.com \
  --restart unless-stopped \
  ghcr.io/bintangtimurlangit/superslice:latest
```

### Docker Compose (Production)

Create a `docker-compose.yml`:

```yaml
version: "3.8"

services:
  superslice:
    image: ghcr.io/bintangtimurlangit/superslice:1.0.0
    container_name: superslice
    ports:
      - "8000:8000"
    environment:
      - SLICE_TIMEOUT=180
      - MAX_FILE_SIZE=104857600
      - CORS_ORIGINS=https://yourdomain.com
    volumes:
      - uploads:/app/uploads
      - output:/app/output
    restart: unless-stopped
    healthcheck:
      test:
        [
          "CMD",
          "python3",
          "-c",
          "import urllib.request; urllib.request.urlopen('http://localhost:8000/')",
        ]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  uploads:
  output:
```

Then run:

```bash
docker-compose up -d
```

### Behind Nginx Reverse Proxy

Example Nginx configuration:

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Increase timeout for large file uploads
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
    }
}
```

### Cloud Platforms

#### AWS ECS/Fargate

Use the GHCR image in your task definition:

```json
{
  "image": "ghcr.io/bintangtimurlangit/superslice:1.0.0",
  "portMappings": [
    {
      "containerPort": 8000,
      "protocol": "tcp"
    }
  ]
}
```

#### Google Cloud Run

```bash
gcloud run deploy superslice \
  --image ghcr.io/bintangtimurlangit/superslice:1.0.0 \
  --platform managed \
  --port 8000 \
  --allow-unauthenticated
```

#### Azure Container Instances

```bash
az container create \
  --resource-group myResourceGroup \
  --name superslice \
  --image ghcr.io/bintangtimurlangit/superslice:1.0.0 \
  --ports 8000 \
  --dns-name-label superslice-api
```

## Monitoring

Check container health:

```bash
docker ps
docker logs superslice
```

Access API documentation:

- Swagger UI: http://your-server:8000/docs
- ReDoc: http://your-server:8000/redoc

## Updating

To update to a new version:

```bash
docker pull ghcr.io/bintangtimurlangit/superslice:latest
docker-compose down
docker-compose up -d
```

## Troubleshooting

### Image Pull Issues

If you can't pull the image, ensure it's set to public visibility in GitHub package settings.

### Port Already in Use

Change the port mapping in docker-compose.yml:

```yaml
ports:
  - "8080:8000" # Use port 8080 instead
```

### Permission Issues

Ensure Docker has proper permissions to create volumes and bind ports.
