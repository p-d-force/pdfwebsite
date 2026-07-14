"""
Browser automation skill for analyzing website behavior.
Uses Selenium to automate Chrome browser and analyze URL changes.
"""
from __future__ import annotations

import time
import re
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse, urljoin

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

from .common import read_json, write_json, ROOT


class BrowserAnalyzer:
    """Analyzes website behavior using browser automation."""
    
    def __init__(self, headless: bool = False, implicit_wait: int = 10):
        """Initialize browser analyzer.
        
        Args:
            headless: Run browser in headless mode
            implicit_wait: Default wait time for element finding
        """
        self.headless = headless
        self.implicit_wait = implicit_wait
        self.driver: Optional[webdriver.Chrome] = None
        self.results: List[Dict[str, Any]] = []
        
    def start_browser(self):
        """Start Chrome browser with appropriate options."""
        if not SELENIUM_AVAILABLE:
            raise ImportError("Selenium not installed. Install with: pip install selenium")
            
        from selenium.webdriver.chrome.options import Options
        
        options = Options()
        if self.headless:
            options.add_argument("--headless")
        
        # Add additional options for better automation
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.implicitly_wait(self.implicit_wait)
        
    def stop_browser(self):
        """Stop browser if running."""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def analyze_url_changes(self, base_url: str, max_links: int = 10) -> List[Dict[str, Any]]:
        """Analyze URL changes when clicking links on a page.
        
        Args:
            base_url: Starting URL to analyze
            max_links: Maximum number of links to click
            
        Returns:
            List of analysis results for each link clicked
        """
        if not self.driver:
            self.start_browser()
        
        self.results = []
        self.driver.get(base_url)
        time.sleep(2)  # Wait for page load
        
        # Get initial page info
        initial_url = self.driver.current_url
        initial_title = self.driver.title
        
        # Find all links on page
        links = self.driver.find_elements(By.TAG_NAME, "a")
        print(f"Found {len(links)} links on page")
        
        # Filter and collect link info
        link_info = []
        for idx, link in enumerate(links[:max_links]):
            try:
                href = link.get_attribute("href")
                text = link.text.strip() or link.get_attribute("innerText").strip()[:50]
                if href and href.startswith("http"):
                    link_info.append({
                        "index": idx,
                        "href": href,
                        "text": text,
                        "element": link
                    })
            except:
                continue
        
        print(f"Processing {len(link_info)} valid links")
        
        # Click each link and analyze behavior
        for link_data in link_info:
            result = self._analyze_link_click(link_data, initial_url)
            self.results.append(result)
            
            # Return to original page
            self.driver.back()
            time.sleep(1)
        
        return self.results
    
    def _analyze_link_click(self, link_data: Dict[str, Any], initial_url: str) -> Dict[str, Any]:
        """Analyze what happens when clicking a specific link."""
        idx = link_data["index"]
        href = link_data["href"]
        text = link_data["text"]
        element = link_data["element"]
        
        print(f"Clicking link {idx}: {text[:30]}... -> {href}")
        
        result = {
            "link_index": idx,
            "link_text": text,
            "link_href": href,
            "click_timestamp": time.time(),
            "url_changes": []
        }
        
        # Record initial state
        initial_state = {
            "action": "before_click",
            "url": self.driver.current_url,
            "title": self.driver.title
        }
        result["url_changes"].append(initial_state)
        
        try:
            # Click the link
            element.click()
            time.sleep(2)  # Wait for navigation
            
            # Record after click state
            after_state = {
                "action": "after_click",
                "url": self.driver.current_url,
                "title": self.driver.title,
                "is_redirected": self.driver.current_url != href
            }
            result["url_changes"].append(after_state)
            
            # Analyze URL structure
            parsed_url = urlparse(self.driver.current_url)
            result["final_url_analysis"] = {
                "scheme": parsed_url.scheme,
                "netloc": parsed_url.netloc,
                "path": parsed_url.path,
                "params": parsed_url.params,
                "query": parsed_url.query,
                "fragment": parsed_url.fragment,
                "has_public_in_path": "/public" in parsed_url.path,
                "public_position": parsed_url.path.find("/public") if "/public" in parsed_url.path else -1
            }
            
            # Check if we need to navigate further
            current_path = parsed_url.path
            if "/public" in current_path:
                # Try to find what's in the /public directory
                try:
                    # Look for links on the new page
                    page_links = self.driver.find_elements(By.TAG_NAME, "a")
                    public_links = []
                    for link in page_links[:5]:  # Check first 5 links
                        try:
                            link_href = link.get_attribute("href")
                            if link_href and "/public" in link_href:
                                public_links.append({
                                    "text": link.text.strip()[:50],
                                    "href": link_href
                                })
                        except:
                            continue
                    
                    result["public_directory_links"] = public_links
                    
                    # Try to click a link in /public directory
                    if public_links:
                        try:
                            # Click first link in /public
                            first_public_link = self.driver.find_element(
                                By.XPATH, f"//a[contains(@href, '/public')]"
                            )
                            first_public_link.click()
                            time.sleep(1)
                            
                            public_click_state = {
                                "action": "public_directory_click",
                                "url": self.driver.current_url,
                                "title": self.driver.title
                            }
                            result["url_changes"].append(public_click_state)
                            
                            # Go back to /public page
                            self.driver.back()
                            time.sleep(1)
                        except:
                            pass
                            
                except Exception as e:
                    result["public_analysis_error"] = str(e)
            
            # Check for common patterns
            result["analysis"] = self._analyze_url_patterns(self.driver.current_url, initial_url)
            
        except Exception as e:
            result["error"] = str(e)
            result["url_changes"].append({
                "action": "error",
                "error": str(e)
            })
        
        return result
    
    def _analyze_url_patterns(self, current_url: str, initial_url: str) -> Dict[str, Any]:
        """Analyze URL patterns for common issues."""
        parsed_current = urlparse(current_url)
        parsed_initial = urlparse(initial_url)
        
        analysis = {
            "domain_changed": parsed_current.netloc != parsed_initial.netloc,
            "path_changed": parsed_current.path != parsed_initial.path,
            "has_public_in_path": "/public" in parsed_current.path,
            "path_components": parsed_current.path.strip("/").split("/") if parsed_current.path else [],
            "possible_rewrite": False,
            "possible_symlink": False,
            "possible_directory_listing": False
        }
        
        # Check for URL rewrite patterns
        if "/public" in parsed_current.path:
            # Try to determine if this is a rewrite or actual directory
            path_parts = parsed_current.path.strip("/").split("/")
            if "public" in path_parts:
                public_index = path_parts.index("public")
                analysis["public_position"] = public_index
                analysis["path_before_public"] = "/".join(path_parts[:public_index])
                analysis["path_after_public"] = "/".join(path_parts[public_index + 1:])
                
                # Common patterns
                if len(path_parts) == 1 and path_parts[0] == "public":
                    analysis["possible_directory_listing"] = True
                elif public_index == 0 and len(path_parts) > 1:
                    analysis["possible_symlink"] = True
        
        return analysis
    
    def generate_report(self, output_path: Optional[Path] = None) -> Dict[str, Any]:
        """Generate analysis report."""
        if not output_path:
            output_path = ROOT / "data" / "browser_analysis.json"
        
        report = {
            "timestamp": time.time(),
            "total_links_analyzed": len(self.results),
            "results": self.results,
            "summary": self._generate_summary()
        }
        
        write_json(output_path, report)
        return report
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate summary of analysis."""
        if not self.results:
            return {}
        
        total_with_public = sum(1 for r in self.results 
                              if r.get("final_url_analysis", {}).get("has_public_in_path", False))
        
        total_errors = sum(1 for r in self.results if "error" in r)
        
        common_paths = {}
        for result in self.results:
            path = result.get("final_url_analysis", {}).get("path", "")
            if path:
                common_paths[path] = common_paths.get(path, 0) + 1
        
        return {
            "links_with_public_in_url": total_with_public,
            "total_errors": total_errors,
            "most_common_paths": sorted(common_paths.items(), key=lambda x: x[1], reverse=True)[:5],
            "public_url_examples": [
                r["final_url_analysis"]["path"] 
                for r in self.results 
                if r.get("final_url_analysis", {}).get("has_public_in_path", False)
            ][:3]
        }


def analyze_website_urls(url: str = "https://parentdataforce.com", max_links: int = 15) -> Dict[str, Any]:
    """Main function to analyze website URL changes.
    
    Args:
        url: URL to analyze
        max_links: Maximum number of links to click
        
    Returns:
        Analysis report
    """
    analyzer = BrowserAnalyzer(headless=True)
    
    try:
        print(f"Starting analysis of {url}")
        results = analyzer.analyze_url_changes(url, max_links)
        report = analyzer.generate_report()
        
        print(f"Analysis complete. Analyzed {len(results)} links.")
        print(f"Found {report['summary']['links_with_public_in_url']} links with '/public' in URL")
        
        return report
        
    finally:
        analyzer.stop_browser()


if __name__ == "__main__":
    # Example usage
    report = analyze_website_urls("https://parentdataforce.com", max_links=10)
    print(json.dumps(report["summary"], indent=2))