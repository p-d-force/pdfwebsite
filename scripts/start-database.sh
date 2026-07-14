#!/bin/bash
# Start MariaDB and PHP containers for Parent Data Force admin

set -e

cd "$(dirname "$0")/.."

echo "Parent Data Force - Database Setup"
echo "=================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker daemon is not running."
    echo "   Please start Docker Desktop and try again."
    exit 1
fi

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "   Please review the generated .env file and adjust credentials if needed."
fi

echo "📦 Starting Docker containers (MariaDB, PHP, phpMyAdmin)..."
docker-compose up -d

echo "⏳ Waiting for database to be ready (30 seconds)..."
sleep 30

# Run database test
echo "🧪 Testing database connection..."
python backend/test_database.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Database setup completed successfully!"
    echo ""
    echo "Access points:"
    echo "  • phpMyAdmin: http://localhost:8080"
    echo "  • PHP Admin:  http://localhost:8081/admin/login.php"
    echo "  • MariaDB:    localhost:3306"
    echo ""
    echo "Default admin credentials:"
    echo "  Username: admin"
    echo "  Password: admin"
    echo ""
    echo "⚠️  IMPORTANT: Change the default password after first login!"
else
    echo ""
    echo "❌ Database test failed. Check the logs above."
    echo "   You can try: docker-compose logs mariadb"
    exit 1
fi