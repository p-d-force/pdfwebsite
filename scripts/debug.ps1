# Parent Data Force - Debug and Status Script
# Simple PowerShell script to check system status

param(
    [string]$Mode = "status"
)

function Write-Header($title) {
    Write-Host ""
    Write-Host ("=" * 60) -ForegroundColor Cyan
    Write-Host $title -ForegroundColor Cyan
    Write-Host ("=" * 60) -ForegroundColor Cyan
    Write-Host ""
}

function Show-Status {
    Write-Header "SYSTEM STATUS"
    
    # Check Docker
    Write-Host "Docker Status:" -ForegroundColor Yellow
    try {
        docker --version 2>&1 | Out-Null
        Write-Host "  [OK] Docker installed" -ForegroundColor Green
        
        docker info 2>&1 | Out-Null
        Write-Host "  [OK] Docker Desktop running" -ForegroundColor Green
        
        # Check containers
        $containers = docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | Select-String "pdf_"
        if ($containers) {
            Write-Host "  [OK] Containers running:" -ForegroundColor Green
            $containers | ForEach-Object { Write-Host "    $_" -ForegroundColor Gray }
        } else {
            Write-Host "  [ERROR] No containers running" -ForegroundColor Red
        }
    } catch {
        Write-Host "  [ERROR] Docker not running: $_" -ForegroundColor Red
    }
    
    # Check .env file
    Write-Host "`nConfiguration:" -ForegroundColor Yellow
    if (Test-Path ".\.env") {
        Write-Host "  [OK] .env file exists" -ForegroundColor Green
        $env = Get-Content ".\.env" | Select-String "DB_"
        if ($env) {
            Write-Host "  [OK] Database credentials configured" -ForegroundColor Green
        }
    } else {
        Write-Host "  [ERROR] .env file missing" -ForegroundColor Red
    }
    
    # Check admin interface
    Write-Host "`nAdmin Interface:" -ForegroundColor Yellow
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8081/admin/login.php" -Method Head -TimeoutSec 3 -ErrorAction Stop 2>&1
        if ($response.StatusCode -eq 200) {
            Write-Host "  [OK] Admin interface accessible" -ForegroundColor Green
        } else {
            Write-Host "  [ERROR] Admin returned HTTP $($response.StatusCode)" -ForegroundColor Red
        }
    } catch {
        Write-Host "  [ERROR] Cannot reach admin interface" -ForegroundColor Red
    }
    
    # Check phpMyAdmin
    Write-Host "`nphpMyAdmin:" -ForegroundColor Yellow
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8080" -Method Head -TimeoutSec 3 -ErrorAction Stop 2>&1
        if ($response.StatusCode -eq 200) {
            Write-Host "  [OK] phpMyAdmin accessible" -ForegroundColor Green
        } else {
            Write-Host "  [ERROR] phpMyAdmin returned HTTP $($response.StatusCode)" -ForegroundColor Red
        }
    } catch {
        Write-Host "  [WARN] phpMyAdmin not accessible" -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "Quick Commands:" -ForegroundColor Cyan
    Write-Host "  Start:    scripts\start-database.bat" -ForegroundColor Gray
    Write-Host "  Stop:     docker-compose down" -ForegroundColor Gray
    Write-Host "  Logs:     docker-compose logs -f" -ForegroundColor Gray
    Write-Host "  Shell:    docker exec -it pdf_php bash" -ForegroundColor Gray
    Write-Host "  DB:       docker exec -it pdf_mariadb mysql -updf_user -p" -ForegroundColor Gray
    Write-Host ""
}

function Show-Containers {
    Write-Header "DOCKER CONTAINERS"
    
    if (!(Get-Command docker -ErrorAction SilentlyContinue)) {
        Write-Host "[ERROR] Docker not found" -ForegroundColor Red
        return
    }
    
    Write-Host "Container details:" -ForegroundColor Yellow
    docker-compose ps
    
    Write-Host "`nRunning processes:" -ForegroundColor Yellow
    docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"
    
    Write-Host "`nResource usage:" -ForegroundColor Yellow
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.PIDs}}" pdf_mariadb pdf_php pdf_phpmyadmin 2>&1
}

function Show-Database {
    Write-Header "DATABASE STATUS"
    
    # Check if MariaDB is running
    $mariadb = docker ps --format "{{.Names}}" | Select-String "pdf_mariadb"
    if (!$mariadb) {
        Write-Host "[ERROR] MariaDB container not running" -ForegroundColor Red
        return
    }
    
    # Get password from .env
    $envFile = ".\.env"
    if (!(Test-Path $envFile)) {
        Write-Host "[ERROR] .env file not found" -ForegroundColor Red
        return
    }
    
    $envContent = Get-Content $envFile -Raw
    $passwordMatch = [regex]::Match($envContent, "DB_PASSWORD=([^\r\n]+)")
    if (!$passwordMatch.Success) {
        Write-Host "[ERROR] DB_PASSWORD not found in .env" -ForegroundColor Red
        return
    }
    
    $dbPassword = $passwordMatch.Groups[1].Value
    
    Write-Host "Testing database connection..." -ForegroundColor Yellow
    $test = docker exec pdf_mariadb mysql -updf_user -p$dbPassword pdf_db -e "SELECT 'Connection OK' AS status;" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Database connected successfully" -ForegroundColor Green
        
        # Get statistics
        Write-Host "`nDatabase Statistics:" -ForegroundColor Yellow
        
        $stats = @"
docker exec pdf_mariadb mysql -updf_user -p$dbPassword pdf_db -e '
SELECT 
    (SELECT COUNT(*) FROM districts) as districts,
    (SELECT COUNT(*) FROM cases) as cases,
    (SELECT COUNT(*) FROM events) as events,
    (SELECT COUNT(*) FROM documents) as documents,
    (SELECT COUNT(*) FROM admin_users) as admin_users;'
"@
        $result = Invoke-Expression $stats 2>&1
        if ($LASTEXITCODE -eq 0) {
            $lines = $result -split "`n"
            if ($lines.Count -gt 1) {
                $data = $lines[1] -split "`t"
                Write-Host "  Districts: $($data[0])" -ForegroundColor Gray
                Write-Host "  Cases: $($data[1])" -ForegroundColor Gray
                Write-Host "  Events: $($data[2])" -ForegroundColor Gray
                Write-Host "  Documents: $($data[3])" -ForegroundColor Gray
                Write-Host "  Admin Users: $($data[4])" -ForegroundColor Gray
            }
        }
        
        # Show admin user
        $admin = docker exec pdf_mariadb mysql -updf_user -p$dbPassword pdf_db -e "SELECT username, role, password_changed_at FROM admin_users;" 2>&1
        if ($LASTEXITCODE -eq 0) {
            $lines = $admin -split "`n"
            if ($lines.Count -gt 1) {
                $data = $lines[1] -split "`t"
                Write-Host "`nAdmin User:" -ForegroundColor Yellow
                Write-Host "  Username: $($data[0])" -ForegroundColor Gray
                Write-Host "  Role: $($data[1])" -ForegroundColor Gray
                Write-Host "  Password changed: $($data[2])" -ForegroundColor Gray
            }
        }
        
    } else {
        Write-Host "[ERROR] Database connection failed" -ForegroundColor Red
        Write-Host $test -ForegroundColor Red
    }
}

function Show-Logs {
    Write-Header "RECENT LOGS"
    
    Write-Host "Last 10 lines from each container:" -ForegroundColor Yellow
    Write-Host "`nPHP Container:" -ForegroundColor Cyan
    docker-compose logs --tail=10 php 2>&1
    
    Write-Host "`nMariaDB Container:" -ForegroundColor Cyan
    docker-compose logs --tail=10 mariadb 2>&1
    
    Write-Host "`nFollow logs with: docker-compose logs -f" -ForegroundColor Gray
}

function Show-Admin {
    Write-Header "ADMIN INTERFACE TEST"
    
    Write-Host "Testing admin interface at http://localhost:8081/admin/login.php" -ForegroundColor Yellow
    
    try {
        # Get login page
        $page = Invoke-WebRequest -Uri "http://localhost:8081/admin/login.php" -TimeoutSec 5 -ErrorAction Stop
        Write-Host "[OK] Page loaded (HTTP $($page.StatusCode))" -ForegroundColor Green
        
        # Check for form elements
        if ($page.Content -match "login-form") {
            Write-Host "[OK] Login form found" -ForegroundColor Green
        }
        
        if ($page.Content -match "csrf_token") {
            Write-Host "[OK] CSRF protection enabled" -ForegroundColor Green
        }
        
        # Check headers
        Write-Host "`nSecurity Headers:" -ForegroundColor Yellow
        $headers = $page.Headers
        $checkHeaders = @("X-Content-Type-Options", "X-Frame-Options", "X-XSS-Protection")
        
        foreach ($h in $checkHeaders) {
            if ($headers[$h]) {
                Write-Host ("  [OK] " + $h + ": " + $headers[$h]) -ForegroundColor Green
            } else {
                Write-Host ("  [WARN] " + $h + ": Not set") -ForegroundColor Yellow
            }
        }
        
    } catch {
        Write-Host "[ERROR] Cannot access admin interface: $_" -ForegroundColor Red
    }
    
    Write-Host "`nAccess URLs:" -ForegroundColor Cyan
    Write-Host "  Admin:      http://localhost:8081/admin/login.php" -ForegroundColor Gray
    Write-Host "  phpMyAdmin: http://localhost:8080" -ForegroundColor Gray
    Write-Host "  Default credentials: admin / (see .env or SETUP-INSTRUCTIONS.md)" -ForegroundColor Gray
}

function Show-All {
    Show-Status
    Show-Containers
    Show-Database
    Show-Admin
    Show-Logs
}

# Main execution
Write-Host ""
Write-Host "PARENT DATA FORCE - DEBUG UTILITY" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green
Write-Host "Time: $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor Gray
Write-Host ""

switch ($Mode.ToLower()) {
    "status" { Show-Status }
    "containers" { Show-Containers }
    "database" { Show-Database }
    "admin" { Show-Admin }
    "logs" { Show-Logs }
    "all" { Show-All }
    default {
        Write-Host "Available modes: status, containers, database, admin, logs, all" -ForegroundColor Yellow
        Show-Status
    }
}

Write-Host ""
Write-Host "Debug complete at $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor Gray