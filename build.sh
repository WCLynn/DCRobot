#!/usr/bin/env bash

# 更新系統套件列表
apt-get update 

# 安裝 ffmpeg
apt-get install -y ffmpeg

# 安裝 Python 依賴
pip install -r requirements.txt