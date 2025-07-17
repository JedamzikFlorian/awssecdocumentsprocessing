#!/bin/bash
echo "🚀 Lifecycle-Skript gestartet"
sudo apt update
sudo apt install -y git
git clone https://github.com/hiyouga/LLaMA-Factory.git /home/sagemaker-user/llama-factory
cd /home/sagemaker-user/llama-factory
pip install -r requirements.txt
echo "✅ Setup abgeschlossen"