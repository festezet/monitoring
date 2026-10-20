#!/usr/bin/env python3
"""
Application de monitoring temps réel - Backend FastAPI
Surveille CPU, GPU, RAM, températures en temps réel
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import psutil
import asyncio
import json
from datetime import datetime
from typing import Dict, List
import os
import logging
from pathlib import Path

# Essayer d'importer nvidia-ml-py3 pour le GPU
try:
    import pynvml
    pynvml.nvmlInit()
    GPU_AVAILABLE = True
except:
    GPU_AVAILABLE = False
    print("⚠️  GPU monitoring non disponible (installer nvidia-ml-py3)")

# Configuration logging menaces mémoire
# Utiliser chemin relatif pour compatibilité Docker
LOG_DIR = Path("/app/logs") if os.path.exists("/app") else Path("/data/projects/PRJ-014-monitoring/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)
MEMORY_THREATS_LOG = LOG_DIR / "memory_threats.log"

# Logger spécifique pour menaces mémoire
memory_logger = logging.getLogger("memory_threats")
memory_logger.setLevel(logging.WARNING)
handler = logging.FileHandler(MEMORY_THREATS_LOG)
handler.setFormatter(logging.Formatter(
    '%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
))
memory_logger.addHandler(handler)

app = FastAPI(title="System Monitor", version="1.0.0")

# CORS pour permettre accès depuis navigateur
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Liste des connexions WebSocket actives
active_connections: List[WebSocket] = []


def get_cpu_stats() -> Dict:
    """Récupère statistiques CPU"""
    cpu_percent = psutil.cpu_percent(interval=0.5, percpu=True)
    cpu_freq = psutil.cpu_freq()

    return {
        "percent_per_core": cpu_percent,
        "percent_avg": sum(cpu_percent) / len(cpu_percent),
        "core_count": len(cpu_percent),
        "frequency_mhz": cpu_freq.current if cpu_freq else 0,
        "frequency_max_mhz": cpu_freq.max if cpu_freq else 0,
    }


def get_memory_stats() -> Dict:
    """Récupère statistiques RAM"""
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()

    return {
        "total_gb": round(mem.total / (1024**3), 2),
        "used_gb": round(mem.used / (1024**3), 2),
        "available_gb": round(mem.available / (1024**3), 2),
        "percent": mem.percent,
        "swap_total_gb": round(swap.total / (1024**3), 2),
        "swap_used_gb": round(swap.used / (1024**3), 2),
        "swap_percent": swap.percent,
    }


def get_gpu_stats() -> Dict:
    """Récupère statistiques GPU NVIDIA"""
    if not GPU_AVAILABLE:
        return {"available": False}

    try:
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)

        # Utilisation GPU
        util = pynvml.nvmlDeviceGetUtilizationRates(handle)

        # Mémoire VRAM
        mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)

        # Température
        temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)

        # Nom GPU
        name = pynvml.nvmlDeviceGetName(handle)
        if isinstance(name, bytes):
            name = name.decode('utf-8')

        # Power usage
        try:
            power_usage = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000  # mW to W
            power_limit = pynvml.nvmlDeviceGetPowerManagementLimit(handle) / 1000
        except:
            power_usage = 0
            power_limit = 0

        # Processus utilisant le GPU
        gpu_processes = []
        try:
            procs = pynvml.nvmlDeviceGetComputeRunningProcesses(handle)
            for proc in procs:
                try:
                    # Obtenir le nom du processus via psutil
                    p = psutil.Process(proc.pid)
                    proc_name = p.name()
                except:
                    proc_name = f"PID:{proc.pid}"

                gpu_processes.append({
                    "pid": proc.pid,
                    "name": proc_name,
                    "vram_mb": round(proc.usedGpuMemory / (1024**2), 1) if proc.usedGpuMemory else 0
                })
        except:
            pass

        return {
            "available": True,
            "name": name,
            "utilization_percent": util.gpu,
            "memory_utilization_percent": util.memory,
            "memory_total_gb": round(mem_info.total / (1024**3), 2),
            "memory_used_gb": round(mem_info.used / (1024**3), 2),
            "memory_free_gb": round(mem_info.free / (1024**3), 2),
            "temperature_c": temp,
            "power_usage_w": round(power_usage, 1),
            "power_limit_w": round(power_limit, 1),
            "processes": gpu_processes,
        }
    except Exception as e:
        return {"available": False, "error": str(e)}


def get_top_processes(limit: int = 10) -> List[Dict]:
    """Récupère les processus les plus gourmands en CPU/RAM"""
    processes = []

    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'memory_info']):
        try:
            pinfo = proc.info
            processes.append({
                "pid": pinfo['pid'],
                "name": pinfo['name'],
                "cpu_percent": round(pinfo['cpu_percent'] or 0, 1),
                "memory_percent": round(pinfo['memory_percent'] or 0, 1),
                "memory_mb": round(pinfo['memory_info'].rss / (1024**2), 1) if pinfo['memory_info'] else 0,
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    # Trier par CPU (décroissant)
    processes.sort(key=lambda x: x['cpu_percent'], reverse=True)

    return processes[:limit]


def detect_memory_threats() -> Dict:
    """Détecte les processus qui risquent de faire crasher le système (OOM)"""
    mem = psutil.virtual_memory()
    available_gb = mem.available / (1024**3)

    # Seuils critiques
    CRITICAL_THRESHOLD_GB = 1.0  # Si moins de 1 GB disponible
    HIGH_MEMORY_PROCESS_GB = 2.0  # Processus utilisant plus de 2 GB

    threats = []
    critical_alert = False

    # Vérifier si RAM critique
    if available_gb < CRITICAL_THRESHOLD_GB:
        critical_alert = True

    # Trouver processus gourmands en mémoire
    for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'memory_percent']):
        try:
            pinfo = proc.info
            memory_gb = pinfo['memory_info'].rss / (1024**3) if pinfo['memory_info'] else 0

            # Si processus utilise beaucoup de RAM
            if memory_gb > HIGH_MEMORY_PROCESS_GB:
                threats.append({
                    "pid": pinfo['pid'],
                    "name": pinfo['name'],
                    "memory_gb": round(memory_gb, 2),
                    "memory_percent": round(pinfo['memory_percent'] or 0, 1),
                    "risk_level": "critical" if memory_gb > 4.0 else "high"
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    # Trier par mémoire utilisée (décroissant)
    threats.sort(key=lambda x: x['memory_gb'], reverse=True)

    # LOGGING : Enregistrer les menaces dans le fichier log
    if critical_alert:
        memory_logger.critical(
            f"RAM CRITIQUE! {available_gb:.2f} GB disponible (seuil: {CRITICAL_THRESHOLD_GB} GB) | "
            f"Menaces: {len(threats)} processus >2GB"
        )
        for threat in threats[:3]:  # Log top 3
            memory_logger.error(
                f"  ⚠️  PID:{threat['pid']} {threat['name']} utilise {threat['memory_gb']} GB "
                f"({threat['memory_percent']}%) - Niveau: {threat['risk_level']}"
            )
    elif threats:
        # Log warning si processus gourmands détectés (pas critique)
        for threat in threats[:1]:  # Log seulement le pire
            if threat['memory_gb'] > 4.0:
                memory_logger.warning(
                    f"Processus gourmand: PID:{threat['pid']} {threat['name']} "
                    f"utilise {threat['memory_gb']} GB ({threat['memory_percent']}%) - RAM dispo: {available_gb:.2f} GB"
                )

    return {
        "critical_alert": critical_alert,
        "available_gb": round(available_gb, 2),
        "threshold_gb": CRITICAL_THRESHOLD_GB,
        "threats": threats[:5],  # Top 5 menaces
        "threat_count": len(threats)
    }


def get_disk_stats() -> Dict:
    """Récupère statistiques disques"""
    partitions = []

    for partition in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(partition.mountpoint)
            partitions.append({
                "device": partition.device,
                "mountpoint": partition.mountpoint,
                "fstype": partition.fstype,
                "total_gb": round(usage.total / (1024**3), 2),
                "used_gb": round(usage.used / (1024**3), 2),
                "free_gb": round(usage.free / (1024**3), 2),
                "percent": usage.percent,
            })
        except PermissionError:
            continue

    return {"partitions": partitions}


@app.get("/api/stats")
async def get_stats():
    """Endpoint REST pour récupérer toutes les stats"""
    return {
        "timestamp": datetime.now().isoformat(),
        "cpu": get_cpu_stats(),
        "memory": get_memory_stats(),
        "gpu": get_gpu_stats(),
        "disk": get_disk_stats(),
        "top_processes": get_top_processes(10),
        "memory_threats": detect_memory_threats(),
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket pour streaming temps réel des stats"""
    await websocket.accept()
    active_connections.append(websocket)

    try:
        while True:
            # Envoyer stats toutes les 2 secondes
            stats = {
                "timestamp": datetime.now().isoformat(),
                "cpu": get_cpu_stats(),
                "memory": get_memory_stats(),
                "gpu": get_gpu_stats(),
                "top_processes": get_top_processes(5),
                "memory_threats": detect_memory_threats(),
            }

            await websocket.send_json(stats)
            await asyncio.sleep(2)

    except WebSocketDisconnect:
        active_connections.remove(websocket)


@app.get("/api/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "ok",
        "gpu_available": GPU_AVAILABLE,
        "active_connections": len(active_connections),
    }


# Monter les fichiers statiques (frontend)
# Chercher d'abord dans le même dossier (Docker), puis dans ../frontend (dev local)
frontend_path = os.path.join(os.path.dirname(__file__), "frontend")
if not os.path.exists(frontend_path):
    frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")

if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")

    @app.get("/")
    async def read_root():
        return FileResponse(os.path.join(frontend_path, "index.html"))


if __name__ == "__main__":
    import uvicorn
    print("🚀 Démarrage serveur monitoring sur http://localhost:8888")
    print(f"📊 GPU disponible : {GPU_AVAILABLE}")
    uvicorn.run(app, host="0.0.0.0", port=8888, log_level="info")
