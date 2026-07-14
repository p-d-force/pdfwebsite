"""
URL analyzer for investigating website URL changes and /public directory issues.
Uses HTTP requests to analyze redirects and URL patterns without browser automation.
"""
from __future__ import annotations

import time
import json
import requests
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse, urljoin
import re

from .common import read_json, write_json, ROOT


class URLAnalyzer:
    """Analyzes URL behavior using HTTP requests."""
    
    def __init__(self, timeout: int = 10):
        """Initialize URL analyzer.
        
        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        self.results: List[Dict[str, Any]] = []
        
    def analyze_url_behavior(self, url: str) -> Dict[str, Any]:
        """Analyze URL behavior including redirects.
        
        Args:
            url: URL to analyze
            
        Returns:
            Analysis results
        """
        result = {
            "url": url,
            "timestamp": time.time(),
            "redirects": [],
            "final_url": None,
            "status_code": None,
            "has_public_in_path": False,
            "analysis": {}
        }
        
        try:
            response = self.session.get(url, timeout=self.timeout, allow_redirects=True)
            result["status_code"] = response.status_code
            result["final_url"] = response.url
            
            # Check for /public in final URL
            parsed_url = urlparse(response.url)
            result["has_public_in_path"] = "/public" in parsed_url.path
            
            # Analyze URL structure
            result["url_analysis"] = {
                "scheme": parsed_url.scheme,
                "netloc": parsed_url.netloc,
                "path": parsed_url.path,
                "params": parsed_url.params,
                "query": parsed_url.query,
                "fragment": parsed_url.fragment,
                "public_position": parsed_url.path.find("/public") if "/public" in parsed_url.path else -1
            }
            
            # Get redirect history
            if response.history:
                for hist in response.history:
                    result["redirects"].append({
                        "url": hist.url,
                        "status_code": hist.status_code,
                        "headers": dict(hist.headers)
                    })
            
            # Try to extract links from HTML
            if "text/html" in response.headers.get("content-type", ""):
                result["links"] = self._extract_links(response.text, response.url)
            
            # Perform analysis
            result["analysis"] = self._analyze_url_patterns(response.url, url)
            
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    def _extract_links(self, html: str, base_url: str) -> List[Dict[str, str]]:
        """Extract links from HTML content."""
        links = []
        
        # Simple regex for href extraction
        href_pattern = r'href=["\']([^"\']+)["\']'
        for match in re.finditer(href_pattern, html, re.IGNORECASE):
            href = match.group(1)
            if href.startswith(('http://', 'https://', '/', '#')):
                # Resolve relative URLs
                if href.startswith('/'):
                    full_url = urljoin(base_url, href)
                elif not href.startswith(('http://', 'https://')):
                    # Skip anchors and javascript
                    if href.startswith('#') or href.startswith('javascript:'):
                        continue
                    full_url = urljoin(base_url, href)
                else:
                    full_url = href
                
                links.append({
                    "href": href,
                    "full_url": full_url,
                    "has_public": "/public" in full_url
                })
        
        return links[:50]  # Limit to first 50 links
    
    def _analyze_url_patterns(self, final_url: str, initial_url: str) -> Dict[str, Any]:
        """Analyze URL patterns for common issues."""
        parsed_final = urlparse(final_url)
        parsed_initial = urlparse(initial_url)
        
        analysis = {
            "domain_changed": parsed_final.netloc != parsed_initial.netloc,
            "path_changed": parsed_final.path != parsed_initial.path,
            "has_public_in_path": "/public" in parsed_final.path,
            "path_components": parsed_final.path.strip("/").split("/") if parsed_final.path else [],
            "is_redirected": final_url != initial_url,
            "possible_configurations": []
        }
        
        # Check for common web server configurations
        if "/public" in parsed_final.path:
            path_parts = parsed_final.path.strip("/").split("/")
            
            if "public" in path_parts:
                public_index = path_parts.index("public")
                
                # Common configuration patterns
                if public_index == 0:
                    # Root is /public directory
                    analysis["possible_configurations"].append("document_root_is_public")
                    if len(path_parts) == 1:
                        analysis["possible_configurations"].append("public_directory_listing")
                elif public_index > 0:
                    # /public is a subdirectory
                    analysis["possible_configurations"].append("public_is_subdirectory")
                    
                    # Check if there's a symlink or alias
                    if parsed_initial.path and "/public" not in parsed_initial.path:
                        analysis["possible_configurations"].append("url_rewrite_or_alias")
        
        # Check for common web server setups
        common_public_paths = [
            "/public",
            "/public_html",
            "/www",
            "/htdocs",
            "/httpdocs"
        ]
        
        for common_path in common_public_paths:
            if common_path in parsed_final.path:
                analysis["possible_configurations"].append(f"contains_{common_path.strip('/')}")
        
        return analysis
    
    def analyze_site_structure(self, base_url: str, max_pages: int = 10) -> List[Dict[str, Any]]:
        """Analyze site structure by following links.
        
        Args:
            base_url: Starting URL
            max_pages: Maximum number of pages to analyze
            
        Returns:
            List of analysis results
        """
        self.results = []
        visited_urls = set()
        
        # Start with base URL
        to_visit = [base_url]
        
        while to_visit and len(self.results) < max_pages:
            url = to_visit.pop(0)
            
            if url in visited_urls:
                continue
                
            visited_urls.add(url)
            
            print(f"Analyzing: {url}")
            result = self.analyze_url_behavior(url)
            self.results.append(result)
            
            # Add new links to visit
            if "links" in result:
                for link in result["links"]:
                    link_url = link["full_url"]
                    
                    # Only follow links within same domain
                    if (urlparse(link_url).netloc == urlparse(base_url).netloc and
                        link_url not in visited_urls and
                        link_url not in to_visit and
                        len(self.results) + len(to_visit) < max_pages):
                        to_visit.append(link_url)
            
            time.sleep(0.5)  # Be polite
        
        return self.results
    
    def generate_report(self, output_path: Optional[Path] = None) -> Dict[str, Any]:
        """Generate analysis report."""
        if not output_path:
            output_path = ROOT / "data" / "url_analysis.json"
        
        report = {
            "timestamp": time.time(),
            "total_pages_analyzed": len(self.results),
            "results": self.results,
            "summary": self._generate_summary()
        }
        
        write_json(output_path, report)
        return report
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate summary of analysis."""
        if not self.results:
            return {}
        
        # Count URLs with /public in path
        urls_with_public = []
        for result in self.results:
            if result.get("has_public_in_path", False):
                urls_with_public.append(result["final_url"])
        
        # Count redirects
        total_redirects = sum(len(r.get("redirects", [])) for r in self.results)
        
        # Find common configurations
        configurations = {}
        for result in self.results:
            for config in result.get("analysis", {}).get("possible_configurations", []):
                configurations[config] = configurations.get(config, 0) + 1
        
        return {
            "total_urls_with_public": len(urls_with_public),
            "urls_with_public": urls_with_public[:5],  # Limit to 5 examples
            "total_redirects": total_redirects,
            "common_configurations": sorted(configurations.items(), key=lambda x: x[1], reverse=True),
            "sample_urls_analyzed": [r["url"] for r in self.results[:5]]
        }


def analyze_site_urls(base_url: str = "https://parentdataforce.com", max_pages: int = 15) -> Dict[str, Any]:
    """Main function to analyze site URL behavior.
    
    Args:
        base_url: URL to analyze
        max_pages: Maximum number of pages to analyze
        
    Returns:
        Analysis report
    """
    analyzer = URLAnalyzer(timeout=15)
    
    print(f"Starting analysis of {base_url}")
    results = analyzer.analyze_site_structure(base_url, max_pages)
    report = analyzer.generate_report()
    
    print(f"Analysis complete. Analyzed {len(results)} pages.")
    print(f"Found {report['summary']['total_urls_with_public']} URLs with '/public' in path")
    
    # Print key findings
    if report['summary']['total_urls_with_public'] > 0:
        print("\nURLs with /public in path:")
        for url in report['summary']['urls_with_public']:
            print(f"  - {url}")
    
    return report


def test_specific_urls(urls: List[str]) -> List[Dict[str, Any]]:
    """Test specific URLs for /public directory issues.
    
    Args:
        urls: List of URLs to test
        
    Returns:
        List of analysis results
    """
    analyzer = URLAnalyzer()
    results = []
    
    for url in urls:
        print(f"Testing: {url}")
        result = analyzer.analyze_url_behavior(url)
        results.append(result)
        
        if result.get("has_public_in_path", False):
            print(f"  -> Contains /public: {result['final_url']}")
        elif "error" in result:
            print(f"  -> Error: {result['error']}")
        else:
            print(f"  -> No /public found")
        
        time.sleep(0.5)
    
    return results


if __name__ == "__main__":
    # Example usage
    print("Testing parentdataforce.com URL behavior...")
    
    # Test main URL
    analyzer = URLAnalyzer()
    result = analyzer.analyze_url_behavior("https://parentdataforce.com")
    
    print(f"Initial URL: https://parentdataforce.com")
    print(f"Final URL: {result.get('final_url', 'N/A')}")
    print(f"Contains /public: {result.get('has_public_in_path', False)}")
    
    if result.get("has_public_in_path", False):
        print("\nAnalysis of /public path:")
        analysis = result.get("analysis", {})
        for key, value in analysis.items():
            if isinstance(value, list) and value:
                print(f"  {key}: {value}")
            elif not isinstance(value, list) and value:
                print(f"  {key}: {value}")