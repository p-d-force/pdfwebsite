# PowerShell Command Reference for Phase 3 Development

## Overview
This guide provides Windows PowerShell equivalents for common Linux/macOS commands used in Phase 3 development. Use these commands to avoid compatibility issues.

## Basic File Operations

### Find files
```powershell
# Linux: find . -name "*.php"
Get-ChildItem -Recurse -Filter "*.php"

# Linux: find . -type f -name "*.py" -o -name "*.js"
Get-ChildItem -Recurse -Include "*.py", "*.js" -File
```

### Search file contents
```powershell
# Linux: grep -r "class\|function" --include="*.php" .
Get-ChildItem -Recurse -Filter "*.php" | Select-String "class|function"

# Linux: grep -r "TODO\|FIXME" --include="*.py" .
Get-ChildItem -Recurse -Filter "*.py" | Select-String "TODO|FIXME"

# Case-insensitive search
Get-ChildItem -Recurse -Filter "*.php" | Select-String -Pattern "EntityManager" -CaseSensitive:$false
```

### Text manipulation
```powershell
# Linux: sed -n '/\[Overview\]/,/\[Types\]/p' file.md
Get-Content file.md | Select-String -Pattern '\[Overview\]' -Context 0,20

# Linux: cat file.txt | grep "pattern"
Get-Content file.txt | Select-String "pattern"

# Replace text in file
(Get-Content file.txt) -replace "old", "new" | Set-Content file.txt
```

## Directory Operations

### List files
```powershell
# Linux: ls -la
Get-ChildItem

# Linux: tree /F (shows directory structure)
tree /F

# Recursive listing
Get-ChildItem -Recurse | Format-Table Name, Length, LastWriteTime
```

### Count files
```powershell
# Linux: find . -name "*.php" | wc -l
(Get-ChildItem -Recurse -Filter "*.php").Count
```

## Project-Specific Commands for Phase 3

### Entity file operations
```powershell
# List all entity JSON files
Get-ChildItem data/entities -Recurse -Filter "*.json"

# Count entities by type
$people = (Get-ChildItem data/entities/people -Filter "*.json").Count
$orgs = (Get-ChildItem data/entities/orgs -Filter "*.json").Count
Write-Host "People: $people, Organizations: $orgs"

# Search for specific entity patterns
Get-ChildItem data/entities -Recurse -Filter "*.json" | Select-String -Pattern "attleboro" -CaseSensitive:$false
```

### Database operations
```powershell
# Check if Docker containers are running
docker ps --filter "name=pdf_"

# Run MySQL commands in container
docker exec -it pdf_mariadb mysql -u pdf_user -pdev_password pdf_db

# Import SQL file
docker exec -i pdf_mariadb mysql -u pdf_user -pdev_password pdf_db < backend/enhanced_schema.sql
```

### PHP operations
```powershell
# Run PHP script in Docker container
docker exec -it pdf_php php admin/includes/test_script.php

# Check PHP version
docker exec pdf_php php --version
```

## Useful PowerShell Aliases

Create these in your PowerShell profile (`$PROFILE`):

```powershell
# Quick aliases
function grep { Get-ChildItem -Recurse | Select-String $args }
function findf { Get-ChildItem -Recurse -Filter $args[0] }
function countfiles { param($filter) (Get-ChildItem -Recurse -Filter $filter).Count }

# Project shortcuts
function show-entities { Get-ChildItem data/entities -Recurse -Filter "*.json" | Format-Table Name }
function docker-status { docker ps --filter "name=pdf_" }
function db-shell { docker exec -it pdf_mariadb mysql -u pdf_user -pdev_password pdf_db }
```

## Common Phase 3 Development Tasks

### 1. Entity Extraction Testing
```powershell
# Test entity extraction on a document
docker exec pdf_php php admin/includes/EntityManager.php test_extraction document.txt

# Batch process entity extraction
Get-ChildItem cases -Recurse -Filter "*.txt" | ForEach-Object {
    docker exec pdf_php php admin/includes/EntityManager.php extract_entities $_.FullName
}
```

### 2. Database Schema Updates
```powershell
# Apply enhanced schema
docker exec -i pdf_mariadb mysql -u pdf_user -pdev_password pdf_db < backend/enhanced_schema.sql

# Backup database
docker exec pdf_mariadb mysqldump -u pdf_user -pdev_password pdf_db > backup_$(Get-Date -Format "yyyyMMdd").sql
```

### 3. NLP Model Testing
```powershell
# Run Python NLP script
python scripts/train_entity_model.py --data data/entities --output models/

# Test entity extraction with NLP
python -c "import spacy; nlp = spacy.load('en_core_web_sm'); doc = nlp('Test text'); print([(ent.text, ent.label_) for ent in doc.ents])"
```

## Troubleshooting

### Common Issues and Solutions

**Issue**: "Command not recognized" errors
**Solution**: Use PowerShell equivalents or install missing tools:
```powershell
# Install Chocolatey (Windows package manager)
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Install missing tools via Chocolatey
choco install grep sed findutils -y
```

**Issue**: Path separators in scripts
**Solution**: Use `[System.IO.Path]::Combine()` or forward slashes:
```powershell
# Bad (Linux style): ./admin/includes/file.php
# Good (PowerShell): .\admin\includes\file.php
# Good (cross-platform): Join-Path "admin" "includes" "file.php"
```

**Issue**: Line ending differences
**Solution**: Set proper line endings:
```powershell
# Convert Linux line endings to Windows
Get-Content script.sh | Set-Content script.ps1 -Encoding UTF8

# Or use git to handle line endings
git config --global core.autocrlf true
```

## Phase 3 Implementation Commands

### Week 1-2: Enhanced Entity Foundation
```powershell
# 1. Apply database schema updates
docker exec -i pdf_mariadb mysql -u pdf_user -pdev_password pdf_db < backend/enhanced_schema.sql

# 2. Create EntityEnhanced.php
Copy-Item admin\includes\EntityManager.php admin\includes\EntityEnhanced.php

# 3. Test enhanced entity search
docker exec pdf_php php admin\includes\EntityEnhanced.php test_search "test query"
```

### Quick Reference Card
```
grep pattern             -> Select-String pattern
find . -name "*.php"     -> Get-ChildItem -Recurse -Filter "*.php"
sed 's/old/new/g' file   -> (Get-Content file) -replace "old", "new" | Set-Content file
cat file | head -10      -> Get-Content file | Select-Object -First 10
wc -l file              -> (Get-Content file).Count
```

Save this file and keep it handy during Phase 3 development!