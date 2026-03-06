# System Monitor - Temps Réel

Application de monitoring système temps réel pour surveiller CPU, GPU (NVIDIA), RAM, et processus.

## 🎯 Objectif

Application de monitoring systeme temps reel pour surveiller CPU, GPU (NVIDIA), RAM et processus via interface web WebSocket.

## 🎯 Fonctionnalités

- ✅ **CPU** : Utilisation par cœur + moyenne + fréquence
- ✅ **RAM** : Utilisée, disponible, swap
- ✅ **GPU NVIDIA** : Utilisation, VRAM, température, consommation
- ✅ **Processus** : Top 5 processus gourmands en temps réel
- ✅ **Graphiques temps réel** : Historique sur 2 minutes
- ✅ **Alertes automatiques** : CPU/RAM >90%, Temp GPU >80°C
- ✅ **WebSocket** : Mise à jour toutes les 2 secondes
- ✅ **Responsive** : Fonctionne sur desktop/mobile

## 🚀 Démarrage Rapide

### Option 1 : Docker Compose (Recommandé)

```bash
cd /data/projects/monitoring
docker-compose up -d
```

Accès : http://localhost:8888

### Option 2 : Mode développement (Python direct)

```bash
cd /data/projects/monitoring/backend
pip install -r requirements.txt
python main.py
```

Accès : http://localhost:8888

## 📊 API Endpoints

### REST API
- `GET /api/stats` : Récupère toutes les stats (JSON)
- `GET /api/health` : Health check

### WebSocket
- `WS /ws` : Stream temps réel des stats (update toutes les 2 sec)

## 🛠️ Stack Technique

- **Backend** : FastAPI + Uvicorn
- **Frontend** : HTML/CSS/JavaScript + Chart.js
- **Monitoring** : psutil (CPU/RAM) + nvidia-ml-py3 (GPU)
- **Communication** : WebSocket (temps réel)
- **Déploiement** : Docker + Docker Compose

## 📂 Structure

```
/data/projects/monitoring/
├── backend/
│   ├── main.py              # Application FastAPI
│   ├── requirements.txt     # Dépendances Python
│   └── Dockerfile          # Image Docker
├── frontend/
│   └── index.html          # Interface web
├── docker-compose.yml      # Configuration Docker
└── README.md              # Ce fichier
```

## 🔧 Configuration

### Port
Par défaut : **8888**

Modifier dans `backend/main.py` :
```python
uvicorn.run(app, host="0.0.0.0", port=8888)
```

### Intervalle de mise à jour
Par défaut : **2 secondes**

Modifier dans `backend/main.py` :
```python
await asyncio.sleep(2)  # Changer la valeur
```

## 🎨 Personnalisation

### Alertes
Seuils d'alerte dans `frontend/index.html` fonction `checkAlerts()` :
- CPU : 90%
- RAM : 90%
- GPU Temp : 80°C

### Historique graphiques
Par défaut : **60 points (2 minutes)**

Modifier dans `frontend/index.html` :
```javascript
const MAX_HISTORY = 60;  // Changer la valeur
```

## 📈 Cas d'usage

### Monitoring sessions AI
- Surveiller VRAM Ollama/Stable Diffusion
- Détecter surcharge CPU lors transcription Whisper

### Encodage vidéo Kdenlive
- Vérifier utilisation GPU NVENC
- Surveiller température GPU

### Debugging performance
- Identifier processus gourmands
- Analyser utilisation ressources

## 🐛 Troubleshooting

### GPU non détecté
```bash
# Vérifier nvidia-smi fonctionne
nvidia-smi

# Installer nvidia-ml-py3
pip install nvidia-ml-py3
```

### WebSocket déconnecté
- Vérifier backend actif : `curl http://localhost:8888/api/health`
- Regarder logs Docker : `docker-compose logs -f`

### Permissions insuffisantes
Si erreur accès processus :
```bash
# Lancer en mode privilégié (Docker Compose déjà configuré)
docker-compose up -d
```

## 🔐 Sécurité

**⚠️ IMPORTANT** : Application destinée à usage local uniquement.

- Pas d'authentification
- Accès à tous les processus système
- Ne PAS exposer sur Internet

Pour sécuriser :
1. Utiliser reverse proxy (nginx) avec auth basic
2. Restreindre accès réseau local uniquement
3. Ajouter HTTPS si accès distant

## 📝 Logs

### Docker
```bash
docker-compose logs -f system-monitor
```

### Python direct
Les logs s'affichent directement dans le terminal

## 🚀 Prochaines améliorations possibles

- [ ] Historique sur disque (base de données)
- [ ] Export stats en CSV/JSON
- [ ] Notifications push/email si alertes
- [ ] Support multi-GPU
- [ ] Thème dark mode
- [ ] Graphiques interactifs avancés (zoom, pan)
- [ ] Comparaison historique (hier vs aujourd'hui)

## 📄 Licence

Projet personnel - Usage libre

---

**Créé le** : 2025-11-15
**Stack** : FastAPI + Chart.js + WebSocket
**Objectif** : Monitoring temps réel GPU/CPU pour sessions AI/montage vidéo
