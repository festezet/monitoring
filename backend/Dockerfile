FROM python:3.11-slim

WORKDIR /app

# Installer dépendances système pour nvidia-ml-py3
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copier requirements et installer
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code
COPY . .

# Exposer port
EXPOSE 8888

# Commande de démarrage
CMD ["python", "main.py"]
