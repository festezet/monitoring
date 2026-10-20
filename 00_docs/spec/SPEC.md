# SPEC — System Monitor Temps Réel (PRJ-014)

> Version : 1.0 | Date : 2026-03-18 | Auteur : Claude Code (auto-generated)

## 1. Vision & Contexte

### 1.1 Objectif

Application web de monitoring système temps réel permettant de surveiller les ressources critiques (CPU, GPU NVIDIA, RAM, disques) via une interface WebSocket mise à jour toutes les 2 secondes. Conçue pour superviser les sessions AI (Ollama, Whisper, Stable Diffusion), l'encodage vidéo (Kdenlive avec NVENC), et le debugging performance.

### 1.2 Contexte

Fabrice a besoin d'un tableau de bord léger et réactif pour surveiller les ressources de sa machine (Ryzen 5 4600G + GTX 1080 8GB VRAM). Les outils classiques (htop, nvidia-smi) ne permettent pas de suivre l'évolution historique ni d'avoir une vue graphique synthétique en temps réel. L'application doit détecter les menaces mémoire (processus gourmands risquant d'épuiser la RAM) et logger automatiquement les situations critiques.

### 1.3 Utilisateurs cibles

- **Utilisateur unique** : Fabrice (usage local, pas d'authentification)
- **Cas d'usage primaires** :
  - Sessions AI : surveiller la VRAM lors d'inférences Ollama ou génération d'images
  - Encodage vidéo : vérifier utilisation GPU NVENC + température
  - Debugging : identifier processus gourmands causant ralentissements
  - Prévention OOM : détection proactive des menaces mémoire critiques

## 2. Stack Technique

| Composant | Technologie | Version | Rôle |
|-----------|-------------|---------|------|
| **Backend** | FastAPI | 0.104.1 | API REST + WebSocket serveur |
| **ASGI Server** | Uvicorn | 0.24.0 | Serveur asynchrone production |
| **Monitoring CPU/RAM** | psutil | 5.9.6 | Collecte métriques système |
| **Monitoring GPU** | nvidia-ml-py3 | 7.352.0 | Interface NVML pour GPU NVIDIA |
| **WebSocket** | websockets | 12.0 | Communication temps réel bidirectionnelle |
| **Frontend** | HTML/CSS/JS vanilla | - | Interface utilisateur |
| **Graphiques** | Chart.js | 4.4.0 | Visualisation temps réel (historique 2 min) |
| **Déploiement** | Docker + Docker Compose | - | Conteneurisation avec accès GPU |
| **Port** | 8888 | - | Enregistré dans `port_registry.json` |

## 3. Architecture

### 3.1 Vue d'ensemble

```
┌─────────────────────────────────────────────────────┐
│                    NAVIGATEUR                       │
│  ┌─────────────────────────────────────────────┐   │
│  │          Frontend (index.html)              │   │
│  │  - Chart.js (graphiques temps réel)         │   │
│  │  - WebSocket client (update 2s)             │   │
│  │  - Système d'alertes (CPU/RAM/GPU temp)     │   │
│  └──────────────┬──────────────────────────────┘   │
└─────────────────┼──────────────────────────────────┘
                  │ WS /ws (bidirectionnel)
                  │ HTTP GET /api/stats
                  ▼
┌─────────────────────────────────────────────────────┐
│        FastAPI Backend (main.py)                    │
│  ┌─────────────────────────────────────────────┐   │
│  │  WebSocket Endpoint (/ws)                   │   │
│  │  - Broadcast stats toutes les 2s            │   │
│  │  - Gestion connexions actives               │   │
│  ├─────────────────────────────────────────────┤   │
│  │  REST Endpoints                             │   │
│  │  - GET /api/stats (snapshot complet)        │   │
│  │  - GET /api/health (health check)           │   │
│  └──────────────┬──────────────────────────────┘   │
└─────────────────┼──────────────────────────────────┘
                  │
     ┌────────────┼────────────┐
     ▼            ▼            ▼
┌─────────┐ ┌──────────┐ ┌─────────────┐
│ psutil  │ │ pynvml   │ │ filesystem  │
│ CPU/RAM │ │ GPU      │ │ logs/       │
│ Process │ │ NVIDIA   │ │ memory_     │
│ Disk    │ │ GTX 1080 │ │ threats.log │
└─────────┘ └──────────┘ └─────────────┘
```

**Communication asynchrone** : FastAPI async + WebSocket permettent de gérer plusieurs connexions simultanées sans blocage. Le backend collecte les métriques toutes les 2 secondes et les diffuse à tous les clients connectés.

**Détection menaces mémoire** : fonction `detect_memory_threats()` appelée à chaque cycle, logging automatique dans `/app/logs/memory_threats.log` (Docker) ou `/data/projects/PRJ-014-monitoring/logs/memory_threats.log` (local).

### 3.2 Structure des fichiers

```
/data/projects/PRJ-014-monitoring/
├── backend/
│   ├── main.py              # Application FastAPI (335 lignes)
│   ├── requirements.txt     # Dépendances Python
│   └── Dockerfile          # Image Docker backend
├── frontend/
│   └── index.html          # Interface web SPA (593 lignes)
├── logs/                    # Logs menaces mémoire
│   └── memory_threats.log
├── cli.py                   # Interface ligne de commande (170 lignes)
├── docker-compose.yml      # Configuration Docker GPU-enabled
├── test_memory_load.py     # Script test charge mémoire
├── test_memory_real.py     # Script test détection menaces
└── README.md               # Documentation utilisateur
```

## 4. Modèle de Données

### 4.1 Structures JSON (WebSocket/API)

**Message WebSocket (envoyé toutes les 2s)** :
```json
{
  "timestamp": "2026-03-18T14:32:15.123456",
  "cpu": {
    "percent_per_core": [12.5, 8.2, 15.3, 9.1, 10.7, 7.8, 14.2, 11.5, 9.3, 8.7, 12.1, 10.4],
    "percent_avg": 10.8,
    "core_count": 12,
    "frequency_mhz": 3600.5,
    "frequency_max_mhz": 4200.0
  },
  "memory": {
    "total_gb": 15.55,
    "used_gb": 8.23,
    "available_gb": 7.32,
    "percent": 52.9,
    "swap_total_gb": 8.0,
    "swap_used_gb": 0.12,
    "swap_percent": 1.5
  },
  "gpu": {
    "available": true,
    "name": "NVIDIA GeForce GTX 1080",
    "utilization_percent": 35,
    "memory_utilization_percent": 42,
    "memory_total_gb": 8.0,
    "memory_used_gb": 3.36,
    "memory_free_gb": 4.64,
    "temperature_c": 58,
    "power_usage_w": 125.3,
    "power_limit_w": 180.0,
    "processes": [
      {"pid": 12345, "name": "ollama", "vram_mb": 3200.5}
    ]
  },
  "top_processes": [
    {"pid": 1234, "name": "chrome", "cpu_percent": 15.2, "memory_percent": 8.3, "memory_mb": 1285.7}
  ],
  "memory_threats": {
    "critical_alert": false,
    "available_gb": 7.32,
    "threshold_gb": 1.0,
    "threats": [
      {"pid": 5678, "name": "electron", "memory_gb": 2.45, "memory_percent": 15.8, "risk_level": "high"}
    ],
    "threat_count": 1
  }
}
```

**Endpoint REST `/api/stats`** : identique au message WebSocket, mais avec ajout de `disk` :
```json
{
  "disk": {
    "partitions": [
      {
        "device": "/dev/mapper/ubuntu--vg-data",
        "mountpoint": "/data",
        "fstype": "ext4",
        "total_gb": 3725.48,
        "used_gb": 2145.32,
        "free_gb": 1580.16,
        "percent": 57.6
      }
    ]
  }
}
```

### 4.2 Logging menaces mémoire

**Fichier** : `logs/memory_threats.log`

**Format** :
```
2026-03-18 14:32:15 | CRITICAL | RAM CRITIQUE! 0.85 GB disponible (seuil: 1.0 GB) | Menaces: 3 processus >2GB
2026-03-18 14:32:15 | ERROR |   ⚠️  PID:1234 chrome utilise 4.25 GB (27.3%) - Niveau: critical
2026-03-18 14:35:22 | WARNING | Processus gourmand: PID:5678 ollama utilise 3.2 GB (20.6%) - RAM dispo: 2.15 GB
```

**Niveaux** :
- `CRITICAL` : RAM disponible < 1 GB (risque OOM imminent)
- `ERROR` : Processus individuel > 4 GB (forte menace)
- `WARNING` : Processus individuel > 2 GB (menace modérée)

## 5. Fonctionnalités

### 5.1 Monitoring CPU
- **Utilisation par cœur** : affichage graphique pour chaque core (12 cores Ryzen 5 4600G)
- **Moyenne globale** : indicateur synthétique avec code couleur (vert <70%, orange 70-90%, rouge >90%)
- **Fréquence** : actuelle et maximum
- **Graphique historique** : Chart.js line chart (2 minutes, 60 points)

### 5.2 Monitoring RAM
- **Métriques** : total, utilisé, disponible, swap
- **Affichage** : GB + pourcentage + code couleur
- **Graphique historique** : évolution utilisation (2 min)
- **Alertes automatiques** : notification visuelle si >90%

### 5.3 Monitoring GPU NVIDIA
- **Détection dynamique** : fallback gracieux si GPU indisponible
- **Métriques** :
  - Utilisation GPU + mémoire (%)
  - VRAM : total, utilisé, libre (GB)
  - Température (°C) avec alerte >80°C
  - Consommation électrique (W) vs limite TDP
  - Processus actifs sur GPU (PID, nom, VRAM utilisée)
- **Graphiques** :
  - Utilisation GPU (%)
  - Température (°C)
  - VRAM utilisée (GB)

### 5.4 Monitoring Disques
- **Partitions** : liste toutes les partitions montées
- **Métriques par partition** : total, utilisé, libre (GB), pourcentage
- **Focus LVM** : surveillance spéciale de `/data` (3.7 TB)

### 5.5 Surveillance Processus
- **Top 5 processus** (WebSocket) / **Top 10** (REST API)
- **Tri** : par CPU décroissant
- **Colonnes** : PID, nom, CPU%, RAM%, RAM (MB)
- **Tableau interactif** : mise à jour temps réel

### 5.6 Détection Menaces Mémoire (OOM Prevention)
- **Seuil critique** : RAM disponible < 1 GB → alerte visuelle + logging CRITICAL
- **Détection processus gourmands** : >2 GB → logging WARNING, >4 GB → logging ERROR
- **Affichage frontend** :
  - Bandeau rouge si alerte critique
  - Liste top 5 menaces avec niveau de risque (high/critical)
  - RAM disponible en temps réel
- **Logging automatique** : fichier `memory_threats.log` avec timestamps

### 5.7 Système d'Alertes
**Déclencheurs** :
- CPU > 90% (moyenne)
- RAM > 90%
- GPU température > 80°C
- RAM disponible < 1 GB (menace OOM)

**Affichage** :
- Notification visuelle en haut de page (couleur + icône + message)
- Code couleur sur les valeurs critiques (rouge)
- Bandeau persistant tant que condition active

## 6. API / Interfaces

### 6.1 REST Endpoints

#### `GET /api/stats`
**Description** : Snapshot complet de toutes les métriques (CPU, RAM, GPU, disques, processus, menaces).

**Réponse** : JSON (voir section 4.1)

**Usage** : polling manuel, debugging, intégration externe.

---

#### `GET /api/health`
**Description** : Health check pour vérifier disponibilité du service.

**Réponse** :
```json
{
  "status": "ok",
  "gpu_available": true,
  "active_connections": 2
}
```

**Usage** : Docker health checks, monitoring externe (HomeHub).

### 6.2 WebSocket Endpoint

#### `WS /ws`
**Description** : Stream temps réel des statistiques système (broadcast toutes les 2s).

**Protocole** :
1. Client ouvre connexion WebSocket
2. Serveur accepte et ajoute à `active_connections`
3. Serveur envoie message JSON toutes les 2 secondes
4. Si client déconnecte → retrait de `active_connections`

**Messages** : JSON identique à `/api/stats` sans `disk` (optimisation bandwidth).

**Gestion reconnexion** : frontend tente reconnexion automatique après 3 secondes si déconnexion.

### 6.3 CLI Interface

**Fichier** : `cli.py` (interface ligne de commande)

**Usage** : `python3 cli.py <command> [options]`

**Commandes disponibles** :

| Commande | Description | Arguments | Exemple |
|----------|-------------|-----------|---------|
| `status` | Vue complète du système (CPU, RAM, GPU, alertes) | - | `python3 cli.py status` |
| `cpu` | Détails CPU (moyenne, fréquence, utilisation par cœur) | - | `python3 cli.py cpu` |
| `memory` | Détails mémoire (RAM, swap) | - | `python3 cli.py memory` |
| `gpu` | Détails GPU (utilisation, VRAM, température, processus GPU) | - | `python3 cli.py gpu` |
| `disk` | Usage des partitions disques | - | `python3 cli.py disk` |
| `processes` | Top processus par usage CPU | `--limit N` (défaut: 10) | `python3 cli.py processes --limit 20` |
| `threats` | Détection menaces mémoire (OOM prevention) | - | `python3 cli.py threats` |

**Fonctionnalités** :
- Accès direct aux métriques système sans passer par l'interface web
- Utilise les mêmes fonctions backend que l'API REST/WebSocket
- Formatage terminal avec barres de progression (CPU par cœur)
- Affichage conditionnel du GPU (fallback si indisponible)
- Alertes visuelles pour menaces mémoire critiques

**Cas d'usage** :
- Scripts automatisés (monitoring batch)
- SSH sans X11 (accès distant terminal uniquement)
- Debugging rapide sans ouvrir navigateur
- Logs snapshot système dans scripts

### 6.4 Frontend Routes

#### `GET /`
**Description** : Interface web principale (SPA).

**Fichier** : `frontend/index.html` (593 lignes, embedded CSS + JS).

**Fonctionnalités** :
- WebSocket client avec reconnexion auto
- 6 graphiques Chart.js (CPU avg, CPU cores, RAM, GPU util, GPU temp, GPU VRAM)
- Tableau processus dynamique
- Système d'alertes visuelles
- Responsive design (desktop/mobile)

## 7. Configuration & Déploiement

### 7.1 Docker Compose (Recommandé)

**Fichier** : `docker-compose.yml`

**Configuration GPU** :
```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: all
          capabilities: [gpu, utility]
privileged: true  # Accès complet processus système
pid: host         # Namespace PID hôte (voir tous processus)
```

**Volumes** :
- `./backend:/app` : code backend (hot reload dev)
- `./frontend:/app/frontend:ro` : frontend read-only
- `./logs:/app/logs` : persistance logs menaces

**Démarrage** :
```bash
cd /data/projects/PRJ-014-monitoring
docker-compose up -d
```

**Logs** :
```bash
docker-compose logs -f system-monitor
```

### 7.2 Mode Développement (Python direct)

**Prérequis** :
- Python 3.11+
- CUDA Toolkit installé (pour nvidia-ml-py3)

**Installation** :
```bash
cd /data/projects/PRJ-014-monitoring/backend
pip install -r requirements.txt
```

**Lancement** :
```bash
python main.py
```

**Limitations** : nécessite permissions root pour accéder à tous les processus système (solution : `sudo python main.py` ou Docker).

### 7.3 Configuration

| Paramètre | Fichier | Valeur par défaut | Modification |
|-----------|---------|-------------------|--------------|
| **Port** | `backend/main.py` | 8888 | `uvicorn.run(..., port=XXXX)` |
| **Update interval** | `backend/main.py` | 2s | `await asyncio.sleep(2)` ligne 301 |
| **Historique graphiques** | `frontend/index.html` | 60 points (2 min) | `const MAX_HISTORY = 60` |
| **Seuils alertes** | `frontend/index.html` | CPU 90%, RAM 90%, GPU 80°C | Fonction `checkAlerts()` |
| **Seuil OOM** | `backend/main.py` | RAM < 1 GB | `CRITICAL_THRESHOLD_GB = 1.0` ligne 186 |
| **Seuil processus gourmand** | `backend/main.py` | > 2 GB | `HIGH_MEMORY_PROCESS_GB = 2.0` ligne 187 |

### 7.4 Enregistrement Port

**Port 8888** enregistré dans `/data/projects/infrastructure/data/port_registry.json` :
```json
{
  "port": 8888,
  "service": "System Monitor",
  "project": "monitoring",
  "stack": "projects",
  "protocol": "HTTP/WS",
  "bind": "0.0.0.0",
  "config_file": "monitoring/backend/main.py",
  "notes": "Real-time system monitoring (CPU/GPU/RAM/disk)"
}
```

## 8. Exigences Non-Fonctionnelles

### 8.1 Performance
- **Latence WebSocket** : < 100 ms par message (2 secondes entre updates)
- **CPU overhead monitoring** : < 2% CPU moyen (collecte métriques)
- **Mémoire backend** : < 150 MB RAM (FastAPI + psutil + pynvml)
- **Concurrence** : support 10+ connexions WebSocket simultanées sans dégradation

### 8.2 Fiabilité
- **Uptime cible** : 99% (Docker restart `unless-stopped`)
- **Gestion erreurs** :
  - Fallback gracieux si GPU indisponible (mode CPU/RAM only)
  - Gestion `PermissionError` sur processus protégés (skip silencieux)
  - Reconnexion auto WebSocket côté client (3s delay)
- **Logging menaces** : rotation automatique (à implémenter si volume important)

### 8.3 Sécurité
- **⚠️ PAS d'authentification** : application usage local uniquement
- **Exposition données sensibles** : liste complète processus système accessible
- **Recommandations** :
  - Ne JAMAIS exposer sur Internet
  - Bind `127.0.0.1` si besoin restreindre (actuellement `0.0.0.0` pour réseau local)
  - Ajouter reverse proxy nginx + auth basic si accès distant nécessaire
- **Privilèges Docker** : `privileged: true` + `pid: host` nécessaires pour accès complet processus (risque sécurité acceptable en local)

### 8.4 Maintenabilité
- **Code quality** :
  - Backend : 335 lignes (bien en dessous du seuil 500 lignes)
  - Fonctions < 50 lignes (conformité `.claude/rules/code-modularity.md`)
  - Docstrings sur toutes fonctions publiques
- **Documentation** :
  - README.md complet avec cas d'usage et troubleshooting
  - Comments inline sur logique complexe (détection menaces, parsing GPU)
- **Tests** :
  - `test_memory_load.py` : simulation charge mémoire
  - `test_memory_real.py` : validation détection menaces
  - À ajouter : tests unitaires FastAPI endpoints

### 8.5 Évolutivité
**Améliorations futures identifiées** (README ligne 165-173) :
- Historique persistant (base de données SQLite)
- Export stats CSV/JSON
- Notifications push/email si alertes
- Support multi-GPU
- Dark mode
- Graphiques avancés (zoom, pan)
- Comparaison historique (baseline vs actuel)

### 8.6 Compatibilité
- **OS** : Linux uniquement (dépendance psutil + nvidia-ml-py3)
- **GPU** : NVIDIA avec drivers CUDA (testé GTX 1080, Compute 6.1)
- **Navigateurs** : Chrome/Firefox/Safari modernes (WebSocket + Chart.js 4.4.0)
- **Python** : 3.11+ (FastAPI async features)

---

**Notes d'implémentation** :
- Projet créé le 2025-11-15 pour répondre au besoin de monitoring GPU lors des sessions AI (Ollama, Whisper)
- Stack volontairement simple (pas de DB, pas de framework JS frontend) pour facilité maintenance
- Détection menaces mémoire ajoutée après incident OOM lors d'inférence Ollama + Chrome avec 50+ onglets
- Logging automatique permet post-mortem après crashes système
