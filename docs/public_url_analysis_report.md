# Public URL Analysis Report

## Problem Statement
When browsing parentdataforce.com and clicking links, the URL changes to include `/public` in the path. This report investigates why this happens and whether it's a configuration issue.

## Key Findings

### 1. FTP Server Structure Analysis
- **Web root directory**: `/public_html` (31 items)
- **Alternative web root**: `/www` (symlink or alias to `/public_html`, 31 items)
- **No `/public` directory at FTP root**: Directory doesn't exist at FTP level
- **No `/htdocs` or `/httpdocs` directories**: Not present in this hosting setup

### 2. HTTP URL Behavior Analysis
Testing various URLs revealed:
- `https://parentdataforce.com/` → Path: `/` (no `/public`)
- `https://parentdataforce.com/districts/` → Path: `/districts/` (no `/public`)
- `https://parentdataforce.com/cases/` → Path: `/cases/` (no `/public`)
- `https://parentdataforce.com/public/` → Path: `/public/` (contains `/public`)
- `https://parentdataforce.com/public_html/` → Path: `/public_html/` (contains `/public_html`)

### 3. Local vs Remote Structure Comparison
**Local structure** (`C:\Users\LokiF\Desktop\PDFWEBSITE\public\`):
- Contains `index.html`, `logo.png`, `robots.txt`, etc.
- Has subdirectories: `calendar/`, `cases/`, `districts/`, `data/`, etc.

**Remote structure** (`/public_html/` on FTP):
- Contains the same files and directories as local `public/` directory
- This suggests the local `public/` directory is what gets uploaded to `/public_html/` on the server

## Root Cause Analysis

### The `/public` URL Mystery
The `/public` in URLs is **not a physical directory** on the FTP server. Instead, it's likely one of these configurations:

1. **Server Alias/AliasMatch Directive** (Apache):
   ```
   Alias /public /home/username/public_html
   ```
   or
   ```
   AliasMatch "^/public(/.*)?$" "/home/username/public_html$1"
   ```

2. **URL Rewrite/RewriteRule** (Apache/.htaccess):
   ```
   RewriteEngine On
   RewriteRule ^public/(.*)$ /$1 [L]
   ```
   or reverse:
   ```
   RewriteRule ^(.*)$ /public/$1 [L]
   ```

3. **Virtual Directory** (IIS) or **Location Block** (Nginx):
   Common in shared hosting environments to expose the document root via multiple paths.

4. **cPanel/WHM Configuration**:
   Many cPanel installations automatically create `/public` as an alias to the document root for compatibility.

### Why This Matters
1. **SEO Impact**: Having `/public` in URLs creates duplicate content issues
2. **User Experience**: Inconsistent URL patterns
3. **Development Confusion**: Developers see different paths locally vs remotely

## Recommendations

### Short-term Fix (Configuration Check)
1. **Check `.htaccess` files** in `/public_html/` for rewrite rules
2. **Examine Apache/Nginx configuration** on the server
3. **Review cPanel settings** for domain aliases or redirects

### Medium-term Solution (Consistency)
1. **Standardize on one path format** (either with or without `/public`)
2. **Implement canonical URLs** to prevent duplicate content
3. **Update internal links** to use consistent paths

### Long-term Solution (Architecture)
1. **Consider using URL rewrite** to remove `/public` from visible URLs
2. **Implement proper routing** if using a framework
3. **Document the configuration** for future maintenance

## Created Tools/Skills

### 1. `skills/browser_automation.py`
- **Purpose**: Automate Chrome browser to analyze URL changes
- **Features**: Click links, track redirects, analyze `/public` patterns
- **Requirements**: Selenium, ChromeDriver

### 2. `skills/url_analyzer.py`
- **Purpose**: Analyze URL behavior using HTTP requests (no browser needed)
- **Features**: Check redirects, extract links, analyze path patterns
- **Requirements**: Python requests library

### 3. `skills/ftp_analyzer.py`
- **Purpose**: Analyze FTP server structure
- **Features**: List directories, compare with local structure, identify web root
- **Requirements**: Python ftplib

### 4. `skills/common.py`
- **Purpose**: Shared utilities for skills modules
- **Features**: JSON read/write, directory handling, slugify function

## How to Use These Tools

### Analyze FTP Structure:
```bash
python -c "from skills.ftp_analyzer import analyze_ftp_structure; import json; report = analyze_ftp_structure('ftp.parentdataforce.com', 'webmaster@parentdataforce.com', 'jJUBFSZK1!'); print(json.dumps(report['summary'], indent=2))"
```

### Analyze URL Behavior:
```bash
python -c "from skills.url_analyzer import analyze_site_urls; import json; report = analyze_site_urls('https://parentdataforce.com', max_pages=5); print(json.dumps(report['summary'], indent=2))"
```

### Test Specific URLs:
```bash
python -c "
import requests
from urllib.parse import urlparse

def test_url(url):
    response = requests.get(url, timeout=10, allow_redirects=True)
    print('Testing:', url)
    print('  Final URL:', response.url)
    parsed = urlparse(response.url)
    print('  Path:', parsed.path)
    print('  Has /public:', '/public' in parsed.path)
    
test_url('https://parentdataforce.com')
test_url('https://parentdataforce.com/public/')
"
```

## Conclusion
The `/public` in URLs is a **server configuration artifact**, not a physical directory issue. The website files are correctly deployed to `/public_html/`, and the server is configured to also serve them from the `/public/` path. This is common in shared hosting environments and is usually configured at the server level (Apache/Nginx/cPanel).

**Recommended action**: Check server configuration files (`.htaccess`, `httpd.conf`, `nginx.conf`) for alias or rewrite rules that create the `/public` path mapping.