# AGENTS.md

## Project Overview

**System Monitoring** is a real-time system monitoring application tracking CPU, GPU (NVIDIA), RAM, and processes via WebSocket streaming. Designed for monitoring AI workloads (Whisper, Ollama, Stable Diffusion) and video encoding sessions.

## Key Facts

- **Author**: Fabrice Estezet
- **Stack**: Python 3, FastAPI, WebSocket, psutil, nvidia-ml-py3, Chart.js
- **Deployment**: Docker Compose
- **License**: Personal use
- **Status**: Production

## Architecture

```
backend/main.py         → FastAPI application with WebSocket endpoint
backend/Dockerfile      → Docker image definition
frontend/index.html     → Single-page dashboard with Chart.js
docker-compose.yml      → Production deployment configuration
```

## API

- `GET /api/stats` - JSON snapshot of all system metrics
- `GET /api/health` - Health check endpoint
- `WS /ws` - WebSocket stream (2-second intervals)

## Metrics Collected

- CPU: per-core utilization, average, frequency
- RAM: used, available, swap
- GPU (NVIDIA): utilization, VRAM, temperature, power consumption
- Processes: top 5 resource consumers

## Skills Demonstrated

- Real-time data streaming with WebSocket
- FastAPI async application design
- NVIDIA GPU monitoring via nvidia-ml-py3
- Docker containerization with Compose
- Frontend data visualization with Chart.js
- System-level monitoring with psutil
