#!/bin/bash

echo "✅ Начинаем установку окружения для Shao Bot..."

# Обновление системы
apt update && apt upgrade -y

# Установка необходимых зависимостей
apt install -y software-properties-common wget curl git

# Установка Python 3.10
add-apt-repository ppa:deadsnakes/ppa -y
apt update
apt install -y python3.10 python3.10-venv python3.10-dev python3.10-distutils

# Установка pip для Python 3.10
wget https://bootstrap.pypa.io/get-pip.py
python3.10 get-pip.py

# Создание и активация виртуального окружения
cd ~/shao_bot || exit
python3.10 -m venv venv
source venv/bin/activate

# Установка Python-библиотек
pip install --upgrade pip
pip install python-dotenv python-telegram-bot==21.0 groq supabase nest_asyncio

echo "✅ Установка завершена!"
echo "👉 Активируйте окружение: source venv/bin/activate"
echo "🚀 Запуск: python main.py"
