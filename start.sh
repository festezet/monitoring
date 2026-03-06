#!/bin/bash
# Script de lancement rapide System Monitor

echo "🚀 Démarrage System Monitor..."

# Vérifier si Docker est actif
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker n'est pas actif. Démarrez Docker d'abord."
    exit 1
fi

# Vérifier si nvidia-docker fonctionne
if ! docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi > /dev/null 2>&1; then
    echo "⚠️  nvidia-docker ne semble pas fonctionnel. Le monitoring GPU peut ne pas marcher."
fi

cd "$(dirname "$0")"

# Arrêter container existant si actif
if docker ps -a | grep -q system-monitor; then
    echo "🛑 Arrêt du container existant..."
    docker-compose down
fi

# Démarrer avec Docker Compose
echo "📦 Construction et démarrage du container..."
docker-compose up -d --build

# Attendre que le service soit prêt
echo "⏳ Attente du démarrage du service..."
sleep 3

# Vérifier que le service répond
if curl -s http://localhost:8888/api/health > /dev/null; then
    echo "✅ System Monitor actif !"
    echo ""
    echo "📊 Interface web : http://localhost:8888"
    echo "🔌 API : http://localhost:8888/api/stats"
    echo ""
    echo "Commandes utiles :"
    echo "  - Logs : docker-compose logs -f"
    echo "  - Arrêter : docker-compose down"
    echo "  - Redémarrer : docker-compose restart"
else
    echo "❌ Erreur : Le service ne répond pas"
    echo "Voir les logs : docker-compose logs"
    exit 1
fi
