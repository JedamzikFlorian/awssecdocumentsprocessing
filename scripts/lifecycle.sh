#!/bin/bash

echo "🚀 Lifecycle-Skript gestartet"

# Logging aktivieren
exec > >(tee -a /var/log/lifecycle.log | logger -t lifecycle-script -s 2>/dev/console) 2>&1

# System-Tools
apt update
apt install -y git curl unzip python3-pip

# ENV-Variablen vorbereiten (optional für EFA/NCCL/torchrun später)
echo "export FI_PROVIDER=efa" >> /etc/environment
echo "export FI_EFA_USE_DEVICE_RDMA=1" >> /etc/environment
echo "export NCCL_DEBUG=INFO" >> /etc/environment
echo "export PYTHONUNBUFFERED=1" >> /etc/environment

# Projektordner vorbereiten
mkdir -p /opt/llama-factory
cd /opt

# LLaMA Factory klonen
git clone https://github.com/hiyouga/LLaMA-Factory.git llama-factory

# Python-Abhängigkeiten
cd /opt/llama-factory
#which pip || apt install -y python3-pip
pip3 install --upgrade pip
pip3 install -r requirements.txt

# Optional: Huggingface Transformers & Accelerate
pip3 install transformers accelerate

# Checkpunkt
echo "✅ LLaMA Factory Umgebung bereit"

# GPU-Check (optional)
nvidia-smi || echo "⚠️ NVIDIA nicht verfügbar"

echo "✅ Lifecycle abgeschlossen"
