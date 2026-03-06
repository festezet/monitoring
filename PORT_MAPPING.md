# Mapping des Ports et Applications Locales

**Dernière mise à jour** : 2025-11-15

Ce fichier documente tous les ports utilisés par les applications et services pour éviter les conflits et tests inutiles.

## Services de Monitoring

| Port | Application | Stack | Description | Status |
|------|-------------|-------|-------------|--------|
| 8888 | System Monitor | Standalone | Dashboard temps réel CPU/GPU/RAM | ✅ Actif |
| 9000 | Portainer | Management | Interface gestion Docker | ✅ Actif |

## AI Stack

| Port | Application | Stack | Description | Status |
|------|-------------|-------|-------------|--------|
| 9001 | Whisper | ai-stack | Transcription audio → texte | ✅ Actif |
| 11434 | Ollama | ai-stack | LLM local (Mistral, Llama) | ✅ Actif |
| 8080 | Open WebUI | ai-stack | Interface web pour Ollama | ⏸️ Arrêté par défaut |

## Media Stack

| Port | Application | Stack | Description | Status |
|------|-------------|-------|-------------|--------|
| 32400 | Plex | media-stack | Serveur média streaming | ✅ Actif |
| 7878 | Radarr | media-stack | Gestionnaire films | ✅ Actif |
| 8989 | Sonarr | media-stack | Gestionnaire séries | ✅ Actif |

## Download Stack

| Port | Application | Stack | Description | Status |
|------|-------------|-------|-------------|--------|
| 8090 | qBittorrent | download-stack | Client torrent | ✅ Actif |
| 9696 | Prowlarr | download-stack | Gestionnaire indexeurs | ✅ Actif |

## Notes Importantes

### Ports à ne PAS tester
- **8888** : Réservé pour System Monitor (ce projet)
- **9000** : Portainer (interface Docker critique)
- **11434** : Ollama (charge VRAM GPU, pas RAM)

### Ports sûrs pour tests de charge
- Aucun service critique ne doit être testé directement
- Les tests de charge mémoire doivent se faire via scripts Python autonomes
- Les services Docker sont visibles via `pid: host` dans le monitoring

### Services utilisant la VRAM (pas RAM)
- **Ollama (11434)** : Charge modèles en VRAM (~5-8 GB)
- Whisper utilise aussi GPU mais temporairement (~713 MiB)

### Recommandations
1. **Avant test de charge** : Vérifier qu'aucun service critique n'est en cours
2. **Monitoring** : System Monitor détecte automatiquement processus >2GB
3. **Logs** : Consulter `/data/projects/monitoring/logs/memory_threats.log` après crash

## Commandes utiles

```bash
# Vérifier tous les ports ouverts
sudo netstat -tlnp

# Vérifier ports Docker spécifiques
docker ps --format "table {{.Names}}\t{{.Ports}}"

# Vérifier charge VRAM (Ollama)
nvidia-smi

# Voir logs menaces mémoire
cat /data/projects/monitoring/logs/memory_threats.log

# Tester charge mémoire (3 GB)
cd /data/projects/monitoring
python3 test_memory_real.py 3
```

## Services à surveiller pour crashs mémoire

### Critiques (peuvent causer OOM)
- **Ollama** : Si modèle trop gros chargé en RAM au lieu de VRAM
- **Plex** : Transcoding vidéo 4K simultanés
- **Python scripts** : Traitement gros datasets (pandas, numpy)

### Sûrs (ne devraient pas crasher)
- Whisper : Utilise GPU, mémoire contrôlée
- Radarr/Sonarr : Faible consommation
- qBittorrent : Mémoire stable
- Prowlarr : Faible consommation

---

**💡 Tip** : En cas de crash système, consulter d'abord `memory_threats.log` pour identifier le coupable
