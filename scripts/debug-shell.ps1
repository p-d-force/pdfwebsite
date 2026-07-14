# Parent Data Force Admin - Debug Shell
# PowerShell script to monitor and debug the database/admin system

param(
    [switch]$Help,
    [switch]$Status,
    [switch]$Containers,
    [switch]$Database,
    [switch]$Admin,
    [switch]$Logs,
    [int]$LogLines = 20,
    [switch]$TestLogin,
    [switch]$All
)

function Show-Help {
    Write-Host @"
Parent Data Force Admin - Debug Shell
=====================================
Monitor and debug the MariaDB/MySQL database and PHP admin system.

Usage: .\debug-shell.ps1 [options]

Options:
  -Help              Show this help message
  -Status            Show overall system status (default if no options)
  -Containers        Show Docker container status
  -Database          Show database connection and stats
  -Admin             Test admin interface access
  -Logs [-LogLines N] Show recent container logs (default 20 lines)
  -TestLogin         Test admin login with current password
  -All               Show all information

Examples:
  .\debug-shell.ps1 -Status
  .\debug-shell.ps1 -Containers -Database
  .\debug-shell.ps1 -Logs -LogLines 50
  .\debug-shell.ps1 -All

Environment:
  Admin Interface: http://localhost:8081/admin/login.php
  phpMyAdmin:      http://localhost:8080
  MariaDB:         localhost:3306
"@
}

function Write-Header($title) {
    Write-Host "`n=== $title ===" -ForegroundColor Cyan
    Write-Host ("=" * ($title.Length + 8)) -ForegroundColor Cyan
}

function Write-Success($message) {
    Write-Host "[OK] $message" -ForegroundColor Green
}

function Write-Error($message) {
    Write-Host "[ERROR] $message" -ForegroundColor Red
}

function Write-Info($message) {
    Write-Host "[INFO] $message" -ForegroundColor Yellow
}

function Show-Status {
    Write-Header "System Status"
    
    # Check Docker Desktop
    $dockerRunning = $false
    try {
        $dockerInfo = docker info 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Docker Desktop is running"
            $dockerRunning = $true
        } else {
            Write-Error "Docker Desktop is not running"
        }
    } catch {
        Write-Error "Docker Desktop is not installed or not running"
    }
    
    # Check containers if Docker is running
    if ($dockerRunning) {
        $containers = docker-compose ps --format json | ConvertFrom-Json -ErrorAction SilentlyContinue
        if ($containers) {
            $running = ($containers | Where-Object { $_.State -eq "running" }).Count
            Write-Info "Containers: $running running out of $($containers.Count) total"
        }
    }
    
    # Check admin interface
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8081/admin/login.php" -Method Head -TimeoutSec 5 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Success "Admin interface is accessible (HTTP 200)"
        } else {
            Write-Error "Admin interface returned HTTP $($response.StatusCode)"
        }
    } catch {
        Write-Error "Admin interface is not accessible: $($_.Exception.Message)"
    }
    
    # Check .env file
    if (Test-Path ".\\.env") {
        Write-Success ".env file exists"
        $envContent = Get-Content ".\\.env" -Raw
        $hasDBPassword = $envContent -match "DB_PASSWORD"
        $hasRootPassword = $envContent -match "DB_ROOT_PASSWORD"
        if ($hasDBPassword -and $hasRootPassword) {
            Write-Success ".env contains database credentials"
        }
    } else {
        Write-Error ".env file not found"
    }
    
    Write-Host "`nQuick Commands:" -ForegroundColor Cyan
    Write-Host "  Start:    scripts\start-database.bat" -ForegroundColor Gray
    Write-Host "  Stop:     docker-compose down" -ForegroundColor Gray
    Write-Host "  Logs:     docker-compose logs -f" -ForegroundColor Gray
    Write-Host "  Shell:    docker exec -it pdf_php bash" -ForegroundColor Gray
    Write-Host "  DB Shell: docker exec -it pdf_mariadb mysql -updf_user -p" -ForegroundColor Gray
}

function Show-Containers {
    Write-Header "Docker Containers"
    
    if (!(Get-Command docker -ErrorAction SilentlyContinue)) {
        Write-Error "Docker is not installed or not in PATH"
        return
    }
    
    try {
        Write-Host "Running containers:" -ForegroundColor Yellow
        docker-compose ps
        
        Write-Host "`nContainer status:" -ForegroundColor Yellow
        $containers = docker-compose ps --format json | ConvertFrom-Json -ErrorAction SilentlyContinue
        foreach ($container in $containers) {
            $statusColor = if ($container.State -eq "running") { "Green" } else { "Red" }
            $health = if ($container.Health -and $container.Health -ne "") { " ($($container.Health))" } else { "" }
            Write-Host "  $($container.Service): $($container.State)$health" -ForegroundColor $statusColor
        }
        
        Write-Host "`nPort mappings:" -ForegroundColor Yellow
        $containers = docker ps --format "{{.Names}}: {{.Ports}}" | grep "pdf_"
        if ($containers) {
            $containers | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
        } else {
            Write-Info "No port mappings found"
        }
    } catch {
        Write-Error "Failed to get container info: $_"
    }
}

function Show-Database {
    Write-Header "Database Status"
    
    if (!(Get-Command docker -ErrorAction SilentlyContinue)) {
        Write-Error "Docker is not installed"
        return
    }
    
    # Check if MariaDB container is running
    $mariadbRunning = docker ps --format "{{.Names}}" | Select-String "pdf_mariadb"
    if (!$mariadbRunning) {
        Write-Error "MariaDB container is not running"
        return
    }
    
    try {
        # Load .env variables
        $envFile = ".\\.env"
        if (!(Test-Path $envFile)) {
            Write-Error ".env file not found"
            return
        }
        
        $envContent = Get-Content $envFile -Raw
        $dbPassword = [regex]::Match($envContent, "DB_PASSWORD=([^\r\n]+)").Groups[1].Value
        if (!$dbPassword) {
            Write-Error "DB_PASSWORD not found in .env"
            return
        }
        
        Write-Info "Testing database connection..."
        
        # Test connection
        $testCmd = "docker exec -i pdf_mariadb mysql -updf_user -p$dbPassword pdf_db -e 'SELECT 1 AS connection_test;'"
        $result = Invoke-Expression $testCmd 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Database connection successful"
            
            # Get database stats
            Write-Host "`nDatabase Statistics:" -ForegroundColor Yellow
            
            $tablesCmd = "docker exec -i pdf_mariadb mysql -updf_user -p$dbPassword pdf_db -e 'SHOW TABLES;'"
            $tables = Invoke-Expression $tablesCmd | Select-Object -Skip 1
            Write-Host "  Tables: $($tables.Count)" -ForegroundColor Gray
            
            $countsCmd = @"
docker exec -i pdf_mariadb mysql -updf_user -p$dbPassword pdf_db -e '
SELECT 
    (SELECT COUNT(*) FROM districts) as districts,
    (SELECT COUNT(*) FROM cases) as cases,
    (SELECT COUNT(*) FROM events) as events,
    (SELECT COUNT(*) FROM documents) as documents,
    (SELECT COUNT(*) FROM admin_users) as admin_users,
    (SELECT COUNT(*) FROM audit_log) as audit_logs;'
"@
            $stats = Invoke-Expression $countsCmd | ConvertFrom-Csv -Delimiter "`t"
            if ($stats) {
                Write-Host "  Districts: $($stats.districts)" -ForegroundColor Gray
                Write-Host "  Cases: $($stats.cases)" -ForegroundColor Gray
                Write-Host "  Events: $($stats.events)" -ForegroundColor Gray
                Write-Host "  Documents: $($stats.documents)" -ForegroundColor Gray
                Write-Host "  Admin Users: $($stats.admin_users)" -ForegroundColor Gray
                Write-Host "  Audit Logs: $($stats.audit_logs)" -ForegroundColor Gray
            }
            
            # Check admin user
            $adminCmd = "docker exec -i pdf_mariadb mysql -updf_user -p$dbPassword pdf_db -e 'SELECT username, role, password_changed_at FROM admin_users;'"
            $admin = Invoke-Expression $adminCmd | ConvertFrom-Csv -Delimiter "`t"
            if ($admin) {
                Write-Host "`nAdmin User:" -ForegroundColor Yellow
                Write-Host "  Username: $($admin.username)" -ForegroundColor Gray
                Write-Host "  Role: $($admin.role)" -ForegroundColor Gray
                Write-Host "  Password changed: $($admin.password_changed_at)" -ForegroundColor Gray
            }
            
        } else {
            Write-Error "Database connection failed: $result"
        }
    } catch {
        Write-Error "Database check failed: $_"
    }
}

function Show-Admin {
    Write-Header "Admin Interface"
    
    try {
        Write-Info "Testing admin interface accessibility..."
        
        # Test basic access
        $response = $null
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8081/admin/login.php" -Method Get -TimeoutSec 10 -ErrorAction Stop
        } catch {
            Write-Error "Cannot connect to admin interface: $($_.Exception.Message)"
            return
        }
        
        if ($response.StatusCode -eq 200) {
            Write-Success "Admin interface is accessible"
            
            # Check for login form
            if ($response.Content -match '<form.*id="login-form"') {
                Write-Success "Login form detected"
            } else {
                Write-Info "Login form not found in response"
            }
            
            # Check for CSRF token
            if ($response.Content -match 'name="csrf_token"') {
                Write-Success "CSRF protection is enabled"
            } else {
                Write-Error "CSRF token not found"
            }
            
            # Check security headers
            Write-Host "`nSecurity Headers:" -ForegroundColor Yellow
            $headers = $response.Headers
            $securityHeaders = @(
                "X-Content-Type-Options",
                "X-Frame-Options", 
                "X-XSS-Protection",
                "Referrer-Policy"
            )
            
            foreach ($header in $securityHeaders) {
                if ($headers[$header]) {
                    Write-Success "  $header: $($headers[$header])"
                } else {
                    Write-Error "  $header: Not set"
                }
            }
            
        } else {
            Write-Error "Admin interface returned HTTP $($response.StatusCode)"
        }
        
        # Test dashboard redirect (should redirect to login)
        Write-Host "`nTesting authentication:" -ForegroundColor Yellow
        try {
            $dashboardResponse = Invoke-WebRequest -Uri "http://localhost:8081/admin/dashboard.php" -Method Get -TimeoutSec 5 -ErrorAction Stop
            if ($dashboardResponse.StatusCode -eq 200) {
                Write-Info "Dashboard accessible (may be logged in)"
            } else {
                Write-Info "Dashboard returned HTTP $($dashboardResponse.StatusCode)"
            }
        } catch {
            Write-Info "Dashboard requires login (expected)"
        }
        
    } catch {
        Write-Error "Admin interface test failed: $_"
    }
}

function Show-Logs($lines) {
    Write-Header "Container Logs (last $lines lines)"
    
    if (!(Get-Command docker -ErrorAction SilentlyContinue)) {
        Write-Error "Docker is not installed"
        return
    }
    
    try {
        Write-Host "PHP Container Logs:" -ForegroundColor Yellow
        docker-compose logs --tail=$lines php
        
        Write-Host "`nMariaDB Container Logs:" -ForegroundColor Yellow
        docker-compose logs --tail=$lines mariadb
        
        Write-Host "`nphpMyAdmin Container Logs:" -ForegroundColor Yellow
        docker-compose logs --tail=$lines phpmyadmin
        
    } catch {
        Write-Error "Failed to get logs: $_"
    }
}

function Test-Login {
    Write-Header "Admin Login Test"
    
    # Get password from .env or instructions
    $password = $null
    $instructions = ".\SETUP-INSTRUCTIONS.md"
    if (Test-Path $instructions) {
        $content = Get-Content $instructions -Raw
        $match = [regex]::Match($content, "password.*`(.*?)`")
        if ($match.Success) {
            $password = $match.Groups[1].Value
        }
    }
    
    if (!$password) {
        Write-Error "Could not find password in SETUP-INSTRUCTIONS.md"
        Write-Info "Password should be in SETUP-INSTRUCTIONS.md"
        $password = "YOUR_LOCAL_ADMIN_PASSWORD"
    }
    
    Write-Info "Testing login with password: $password"
    
    try {
        # First, get login page to get CSRF token
        $loginPage = Invoke-WebRequest -Uri "http://localhost:8081/admin/login.php" -Method Get -TimeoutSec 10 -SessionVariable session
        
        # Extract CSRF token
        $csrfMatch = [regex]::Match($loginPage.Content, 'name="csrf_token" value="([^"]+)"')
        if (!$csrfMatch.Success) {
            Write-Error "CSRF token not found on login page"
            return
        }
        
        $csrfToken = $csrfMatch.Groups[1].Value
        Write-Info "CSRF Token: $csrfToken"
        
        # Prepare login data
        $loginData = @{
            username = "admin"
            password = $password
            csrf_token = $csrfToken
        }
        
        # Attempt login
        Write-Info "Attempting login..."
        $loginResponse = Invoke-WebRequest -Uri "http://localhost:8081/admin/login.php" -Method Post -Body $loginData -WebSession $session -TimeoutSec 10
        
        # Check result
        if ($loginResponse.Content -match "Invalid username or password") {
            Write-Error "Login failed: Invalid username or password"
        } elseif ($loginResponse.Content -match "Invalid security token") {
            Write-Error "Login failed: Invalid CSRF token"
        } elseif ($loginResponse.Content -match "dashboard") {
            Write-Success "Login successful! Redirected to dashboard"
        } else {
            Write-Info "Login response received (check manually)"
            Write-Host "Response status: $($loginResponse.StatusCode)" -ForegroundColor Gray
        }
        
    } catch {
        Write-Error "Login test failed: $($_.Exception.Message)"
    }
}

# Main execution
if ($Help) {
    Show-Help
    exit 0
}

# If no specific flags, show status
if (!$Status -and !$Containers -and !$Database -and !$Admin -and !$Logs -and !$TestLogin -and !$All) {
    $Status = $true
}

if ($All) {
    $Status = $true
    $Containers = $true
    $Database = $true
    $Admin = $true
    $Logs = $true
    $TestLogin = $true
}

Write-Host "`nParent Data Force - Debug Shell" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host "Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
Write-Host "Working Dir: $(Get-Location)" -ForegroundColor Gray
Write-Host ""

if ($Status) { Show-Status }
if ($Containers) { Show-Containers }
if ($Database) { Show-Database }
if ($Admin) { Show-Admin }
if ($Logs) { Show-Logs $LogLines }
if ($TestLogin) { Test-Login }

Write-Host "`nDebug completed at $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor Gray