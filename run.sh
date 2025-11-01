# 启动脚本
#!/bin/bash

if [ -d "backend" ] && [ -f "backend/server.js" ]; then
    echo "Detected backend directory with server.js. Running npm install and node server.js..."
    cd backend
    #npm install
    PORT=3000 node server.js
    cd ..
elif [ -d "backend" ] && [ -f "backend/app.py" ]; then
    # 检查 backend 目录和 app.py 文件
    echo "Detected backend directory with app.py. Running conda environment setup and python app.py..."
    cd backend
    #pip install -r requirements.txt
    PORT=3000 python app.py
    cd ..
elif [ -d "backend" ] && [ -f "backend/streamlit_app.py" ]; then
    cd backend
    #pip install -r requirements.txt
    python -m streamlit run streamlit_app.py --server.port 3000 --global.developmentMode=false
    cd ..
elif [ ! -d "backend" ] || { [ -d "backend" ] && [ "$(ls -A backend | wc -l)" -eq 1 ] && [ -d "backend/node_modules" ]; }; then
    # 如果不存在 backend 目录
    echo "No backend directory found. Running HTTP server in frontend/public directory..."
    if [ -f "frontend/next.config.js" ]; then
        cd frontend
        npm start
    elif [ -d "frontend/public" ]; then
        cd frontend/public
        serve ./ -l 3000 --no-clipboard
    elif [ -d "frontend" ]; then
        echo "No backend directory found. Running HTTP server in frontend directory..."
        cd frontend
        python -m http.server 3000
    else
        echo "No frontend/public directory found. Exiting."
    fi
else
    echo "No backend directory with server.js or app.py found. Exiting."
fi