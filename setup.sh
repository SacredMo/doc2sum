#!/bin/bash

# 安装依赖
pip install -r requirements.txt

# 创建必要的目录
mkdir -p ~/.streamlit/
mkdir -p data/users

# 创建Streamlit配置文件
echo "\
[general]
email = \"your-email@example.com\"
" > ~/.streamlit/credentials.toml

echo "\
[server]
headless = true
enableCORS = false
port = $PORT

[theme]
primaryColor = \"#4CAF50\"
backgroundColor = \"#FFFFFF\"
secondaryBackgroundColor = \"#F0F2F6\"
textColor = \"#262730\"
font = \"sans serif\"
" > ~/.streamlit/config.toml
