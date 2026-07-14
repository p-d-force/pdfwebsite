"""
FTP analyzer for investigating server directory structure.
Helps understand why /public appears in URLs.
"""
from __future__ import annotations

import time
import json
import ftplib
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from .common import read_json, write_json, ROOT


class FTPAnalyzer:
    """Analyzes FTP server structure."""
    
    def __init__(self, host: str, username: str, password: str):
        """Initialize FTP analyzer.
        
        Args:
            host: FTP hostname
            username: FTP username
            password: FTP password
        """
        self.host = host
        self.username = username
        self.password = password
        self.ftp: Optional[ftplib.FTP] = None
        
    def connect(self):
        """Connect to FTP server."""
        self.ftp = ftplib.FTP(self.host)
        self.ftp.login(self.username, self.password)
        self.ftp.set_pasv(True)
        
    def disconnect(self):
        """Disconnect from FTP server."""
        if self.ftp:
            self.ftp.quit()
            self.ftp = None
    
    def list_directory(self, path: str = "/") -> List[str]:
        """List contents of a directory.
        
        Args:
            path: Directory path
            
        Returns:
            List of directory contents
        """
        if not self.ftp:
            self.connect()
        
        contents = []
        self.ftp.cwd(path)
        self.ftp.dir(contents.append)
        
        # Parse directory listing
        parsed_contents = []
        for item in contents:
            parts = item.split()
            if len(parts) >= 9:
                # Extract filename (everything after permissions, links, owner, group, size, date, time)
                filename = " ".join(parts[8:])
                is_dir = item.startswith("d")
                parsed_contents.append({
                    "name": filename,
                    "is_dir": is_dir,
                    "raw": item
                })
        
        return parsed_contents
    
    def analyze_web_structure(self) -> Dict[str, Any]:
        """Analyze web server directory structure.
        
        Returns:
            Analysis of web directory structure
        """
        if not self.ftp:
            self.connect()
        
        result = {
            "timestamp": time.time(),
            "host": self.host,
            "directories": {},
            "analysis": {}
        }
        
        # Check common web directories
        web_dirs = [
            ("/", "root"),
            ("/public_html", "public_html"),
            ("/www", "www"),
            ("/htdocs", "htdocs"),
            ("/httpdocs", "httpdocs"),
            ("/public", "public"),
            ("/public_html/public", "public_inside_public_html")
        ]
        
        for path, name in web_dirs:
            try:
                contents = self.list_directory(path)
                result["directories"][name] = {
                    "path": path,
                    "contents": contents,
                    "count": len(contents)
                }
                print(f"Found {len(contents)} items in {path}")
            except Exception as e:
                result["directories"][name] = {
                    "path": path,
                    "error": str(e),
                    "count": 0
                }
                print(f"Error accessing {path}: {e}")
        
        # Analyze structure
        result["analysis"] = self._analyze_structure(result["directories"])
        
        return result
    
    def _analyze_structure(self, directories: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze directory structure for insights."""
        analysis = {
            "web_root_location": None,
            "public_directory_present": False,
            "public_html_directory_present": False,
            "possible_configurations": [],
            "symlink_possibilities": []
        }
        
        # Check for web root
        if directories.get("public_html", {}).get("count", 0) > 0:
            analysis["web_root_location"] = "public_html"
            analysis["public_html_directory_present"] = True
            
            # Check if index.html exists in public_html
            public_html_contents = directories.get("public_html", {}).get("contents", [])
            has_index = any(item["name"] == "index.html" for item in public_html_contents)
            if has_index:
                analysis["possible_configurations"].append("public_html_is_web_root")
        
        if directories.get("www", {}).get("count", 0) > 0:
            analysis["possible_configurations"].append("www_directory_exists")
            if not analysis["web_root_location"]:
                analysis["web_root_location"] = "www"
        
        # Check for /public directory
        if directories.get("public", {}).get("count", 0) > 0:
            analysis["public_directory_present"] = True
            
            # Check if /public is inside /public_html
            public_inside = directories.get("public_inside_public_html", {})
            if public_inside.get("count", 0) > 0:
                analysis["possible_configurations"].append("public_inside_public_html")
                
                # Check if it's a symlink
                public_contents = directories.get("public", {}).get("contents", [])
                public_inside_contents = public_inside.get("contents", [])
                
                if (len(public_contents) == len(public_inside_contents) and
                    all(p["name"] == pi["name"] for p, pi in zip(public_contents, public_inside_contents))):
                    analysis["symlink_possibilities"].append("public_may_be_symlink_to_public_html/public")
        
        # Check for document root patterns
        root_contents = directories.get("root", {}).get("contents", [])
        web_dirs_in_root = [d for d in root_contents if d["is_dir"] and d["name"] in ["public_html", "www", "htdocs", "httpdocs", "public"]]
        
        if web_dirs_in_root:
            analysis["web_dirs_in_root"] = [d["name"] for d in web_dirs_in_root]
            
            # Common configuration: public_html is web root, public is accessible via URL
            if "public_html" in analysis["web_dirs_in_root"] and analysis["public_directory_present"]:
                analysis["possible_configurations"].append("shared_hosting_typical")
                analysis["possible_configurations"].append("public_may_be_alias_or_symlink")
        
        return analysis
    
    def compare_with_local(self, local_path: Path) -> Dict[str, Any]:
        """Compare FTP structure with local directory.
        
        Args:
            local_path: Local directory to compare
            
        Returns:
            Comparison analysis
        """
        comparison = {
            "timestamp": time.time(),
            "ftp_directories": [],
            "local_directories": [],
            "matches": [],
            "differences": []
        }
        
        # Get FTP structure
        ftp_structure = self.analyze_web_structure()
        
        # Get local structure
        local_dirs = []
        for item in local_path.iterdir():
            if item.is_dir():
                local_dirs.append(item.name)
        
        comparison["local_directories"] = local_dirs
        
        # Check for matches
        public_html_ftp = ftp_structure["directories"].get("public_html", {}).get("contents", [])
        ftp_dir_names = [item["name"] for item in public_html_ftp if item["is_dir"]]
        
        for local_dir in local_dirs:
            if local_dir in ftp_dir_names:
                comparison["matches"].append(local_dir)
            else:
                comparison["differences"].append({
                    "type": "local_only",
                    "name": local_dir
                })
        
        for ftp_dir in ftp_dir_names:
            if ftp_dir not in local_dirs:
                comparison["differences"].append({
                    "type": "ftp_only",
                    "name": ftp_dir
                })
        
        # Check for /public directory contents
        if ftp_structure["analysis"]["public_directory_present"]:
            public_contents = ftp_structure["directories"].get("public", {}).get("contents", [])
            public_names = [item["name"] for item in public_contents if not item["is_dir"]]
            
            # Check if local has public directory
            local_public = local_path / "public"
            if local_public.exists():
                local_public_files = [f.name for f in local_public.iterdir() if f.is_file()]
                
                comparison["public_comparison"] = {
                    "ftp_files": public_names[:10],  # Limit to 10
                    "local_files": local_public_files[:10],
                    "ftp_file_count": len(public_names),
                    "local_file_count": len(local_public_files)
                }
        
        return comparison


def analyze_ftp_structure(host: str, username: str, password: str) -> Dict[str, Any]:
    """Main function to analyze FTP structure.
    
    Args:
        host: FTP hostname
        username: FTP username
        password: FTP password
        
    Returns:
        Analysis report
    """
    analyzer = FTPAnalyzer(host, username, password)
    
    try:
        print(f"Connecting to FTP server: {host}")
        analyzer.connect()
        print("Connected successfully")
        
        print("Analyzing web directory structure...")
        structure = analyzer.analyze_web_structure()
        
        print("Comparing with local directory...")
        comparison = analyzer.compare_with_local(ROOT)
        
        report = {
            "ftp_structure": structure,
            "local_comparison": comparison,
            "summary": _generate_summary(structure, comparison)
        }
        
        output_path = ROOT / "data" / "ftp_analysis.json"
        write_json(output_path, report)
        
        print(f"Analysis saved to {output_path}")
        
        # Print key findings
        print("\n=== KEY FINDINGS ===")
        summary = report["summary"]
        print(f"Web root location: {summary.get('web_root_location', 'Unknown')}")
        print(f"Public directory accessible: {summary.get('public_directory_accessible', False)}")
        print(f"Possible configurations: {', '.join(summary.get('possible_configurations', []))}")
        
        if summary.get("symlink_evidence"):
            print(f"Symlink evidence: {summary['symlink_evidence']}")
        
        return report
        
    finally:
        analyzer.disconnect()


def _generate_summary(structure: Dict[str, Any], comparison: Dict[str, Any]) -> Dict[str, Any]:
    """Generate summary of FTP analysis."""
    analysis = structure.get("analysis", {})
    
    summary = {
        "web_root_location": analysis.get("web_root_location"),
        "public_directory_accessible": analysis.get("public_directory_present", False),
        "public_html_directory_present": analysis.get("public_html_directory_present", False),
        "possible_configurations": analysis.get("possible_configurations", []),
        "symlink_evidence": analysis.get("symlink_possibilities", [])
    }
    
    # Add comparison insights
    matches = comparison.get("matches", [])
    if matches:
        summary["directories_synced"] = matches
    
    differences = comparison.get("differences", [])
    if differences:
        ftp_only = [d["name"] for d in differences if d["type"] == "ftp_only"]
        local_only = [d["name"] for d in differences if d["type"] == "local_only"]
        
        if ftp_only:
            summary["ftp_only_directories"] = ftp_only
        if local_only:
            summary["local_only_directories"] = local_only
    
    return summary


if __name__ == "__main__":
    # Read credentials from deploy_config.json
    config_path = ROOT / "deploy_config.json"
    if config_path.exists():
        config = read_json(config_path)
        ftp_config = config.get("ftp", {})
        
        host = ftp_config.get("server", "ftp.parentdataforce.com")
        username = ftp_config.get("username", "webmaster@parentdataforce.com")
        password = ftp_config.get("password", "jJUBFSZK1!")
        
        print(f"Using FTP credentials from {config_path}")
        print(f"Host: {host}")
        print(f"Username: {username}")
        
        report = analyze_ftp_structure(host, username, password)
        
        # Print important findings
        print("\n=== RECOMMENDATIONS ===")
        summary = report["summary"]
        
        if summary.get("public_directory_accessible"):
            print("✓ /public directory is accessible via FTP")
            print("  This explains why URLs show /public in path")
            
            if "public_may_be_alias_or_symlink" in summary.get("possible_configurations", []):
                print("✓ /public may be an alias or symlink to public_html/public")
                print("  This is common in shared hosting environments")
        
        if summary.get("web_root_location") == "public_html":
            print("✓ Web root appears to be /public_html")
            print("  Files should be uploaded to /public_html directory")
        
    else:
        print(f"Config file not found: {config_path}")
        print("Please create deploy_config.json with FTP credentials")