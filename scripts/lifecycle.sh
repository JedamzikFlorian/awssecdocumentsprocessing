#!/bin/bash

echo "🚀 Lifecycle-Skript gestartet"

# System-Tools
apt update
apt install -y git

# Projektordner vorbereiten
mkdir -p /opt/llama-factory

# Repo klonen
git clone https://github.com/hiyouga/LLaMA-Factory.git /opt/llama-factory
cd /opt/llama-factory

# Pip ggf. installieren
which pip || apt install -y python3-pip

# Abhängigkeiten installieren
pip3 install -r requirements.txt

echo "✅ Setup abgeschlossen"