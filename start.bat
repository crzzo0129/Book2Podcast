@echo off
setlocal enabledelayedexpansion
title Book2Podcast

echo ============================================
echo   Book2Podcast - 书本变播客
echo ============================================
echo.

:: ---- Check Python ----
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 Python，请先安装 Python 3.10+
    pause
    exit /b 1
)
echo [OK] Python 已就绪

:: ---- Check Node.js ----
where node >nul 2>&1
if %errorlevel% neq 0 (
    set "NODE_PATH=C:\Program Files\nodejs"
    if exist "!NODE_PATH!\node.exe" (
        set "PATH=!NODE_PATH!;%PATH%"
        echo [OK] Node.js 已就绪 ^(通过路径查找^)
    ) else (
        echo [错误] 未找到 Node.js，请先安装 Node.js 18+
        echo       下载地址: https://nodejs.org
        pause
        exit /b 1
    )
) else (
    echo [OK] Node.js 已就绪
)

:: ---- Check .env ----
if not exist "%~dp0backend\.env" (
    echo.
    echo [警告] 未找到 backend\.env，正在创建...
    if exist "%~dp0backend\.env.example" (
        copy "%~dp0backend\.env.example" "%~dp0backend\.env" >nul
        echo   已从 .env.example 创建 .env，请编辑填入 DeepSeek API Key
        echo   获取 Key: https://platform.deepseek.com
        notepad "%~dp0backend\.env"
        echo.
        echo   按任意键继续...
        pause >nul
    )
)

:: ---- Install Python deps ----
echo.
echo [检查] Python 依赖...
pip show fastapi >nul 2>&1
if %errorlevel% neq 0 (
    echo   正在安装 Python 依赖...
    pip install -r "%~dp0backend\requirements.txt" -q
    if %errorlevel% neq 0 (
        echo   [错误] Python 依赖安装失败，尝试国内镜像...
        pip install -r "%~dp0backend\requirements.txt" -i https://pypi.tuna.tsinghua.edu.cn/simple -q
    )
    echo [OK] Python 依赖安装完成
) else (
    echo [OK] Python 依赖已满足
)

:: ---- Install Node.js deps ----
echo [检查] Node.js 依赖...
if not exist "%~dp0frontend\node_modules" (
    echo   正在安装 Node.js 依赖...
    cd /d "%~dp0frontend"
    call npm install --silent
    if %errorlevel% neq 0 (
        echo   [错误] npm 安装失败，尝试国内镜像...
        call npm config set registry https://registry.npmmirror.com
        call npm install --silent
    )
    echo [OK] Node.js 依赖安装完成
) else (
    echo [OK] Node.js 依赖已存在
)

:: ---- Start services ----
echo.
echo ============================================
echo   启动服务中...
echo   后端: http://localhost:8000
echo   前端: http://localhost:3000
echo   按 Ctrl+C 停止所有服务
echo ============================================
echo.

cd /d "%~dp0backend"
start "Book2Podcast Backend" cmd /c "title Book2Podcast Backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000"

cd /d "%~dp0frontend"
start "Book2Podcast Frontend" cmd /c "title Book2Podcast Frontend && npm run dev"

:: Wait for services to start
echo   等待服务启动...
timeout /t 8 /nobreak >nul

:: Open browser
start http://localhost:3000

echo.
echo   服务已启动！浏览器已打开 http://localhost:3000
echo   关闭此窗口不会影响服务运行。
echo.
pause
