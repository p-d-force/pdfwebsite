@echo off
REM Start MariaDB and PHP containers for Parent Data Force admin

cd /d "%~dp0\.."

echo Parent Data Force - Database Setup
echo ==================================

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker daemon is not running.
    echo    Please start Docker Desktop and try again.
    pause
    exit /b 1
)

REM Check if .env exists
if not exist .env (
    echo ⚠️  .env file not found. Creating from .env.example...
    copy .env.example .env >nul
    echo    Please review the generated .env file and adjust credentials if needed.
)

echo 📦 Starting Docker containers (MariaDB, PHP, phpMyAdmin)...
call docker-compose up -d

echo ⏳ Waiting for database to be ready (30 seconds)...
timeout /t 30 /nobreak >nul

REM Run database test
echo 🧪 Testing database connection...
python backend\test_database.py

if errorlevel 1 (
    echo.
    echo ❌ Database test failed. Check the logs above.
    echo    You can try: docker-compose logs mariadb
    pause
    exit /b 1
) else (
    echo.
    echo ✅ Database setup completed successfully!
    echo.
    echo Access points:
    echo   • phpMyAdmin: http://localhost:8080
    echo   • PHP Admin:  http://localhost:8081/admin/login.php
    echo   • MariaDB:    localhost:3306
    echo.
    echo Default admin credentials:
    echo   Username: admin
    echo   Password: admin
    echo.
    echo ⚠️  IMPORTANT: Change the default password after first login!
    pause
)