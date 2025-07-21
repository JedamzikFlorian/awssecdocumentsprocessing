#!/bin/bash
echo "🚀 Lifecycle-Skript gestartet"
apt update
apt install -y git
mkdir -p /opt/llama-factory
git clone https://github.com/hiyouga/LLaMA-Factory.git /opt/llama-factory
cd /opt/llama-factory
which pip || apt install -y python3-pip
pip3 install -r requirements.txt
echo "✅ Setup abgeschlossen"