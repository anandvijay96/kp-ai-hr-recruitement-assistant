"""
Selenium-based LinkedIn Profile Verifier
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Uses Selenium WebDriver to scrape Google search results for LinkedIn profiles.
This bypasses Google Custom Search API limitations and gets real search results.
"""

import logging
import re
import time
from typing import Dict, List, Optional, Any
from urllib.parse import quote_plus

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup

try:
    from webdriver_manager.chrome import ChromeDriverManager
    WEBDRIVER_MANAGER_AVAILABLE = True
except ImportError:
    WEBDRIVER_MANAGER_AVAILABLE = False

logger = logging.getLogger(__name__)


class SeleniumLinkedInVerifier:
    """Selenium-based verifier for LinkedIn profiles via Google Search"""
    
    def __init__(self):
        """Initialize Selenium LinkedIn verifier"""
        self.driver = None
        self.linkedin_patterns = [
            r'linkedin\.com/in/([\w-]+)',
            r'linkedin\.com/pub/([\w-]+)',
            r'www\.linkedin\.com/in/([\w-]+)',
            r'www\.linkedin\.com/pub/([\w-]+)',
        ]
    
    def initialize_driver(self, headless: bool = True):
        """
        Initialize Chrome WebDriver (supports Browserless for Railway)
        
        Args:
            headless: Run browser in headless mode (no GUI)
        """
        if self.driver:
            return  # Already initialized
        
        import os
        
        logger.info("Initializing Chrome WebDriver for LinkedIn verification...")
        
        chrome_options = Options()
        
        # Check if Browserless is configured (Railway deployment)
        browserless_endpoint = os.environ.get('BROWSER_WEBDRIVER_ENDPOINT')
        browserless_token = os.environ.get('BROWSER_TOKEN')
        
        if browserless_endpoint and browserless_token:
            # Use Browserless (Railway)
            logger.info("Using Browserless service for Chrome WebDriver")
            chrome_options.set_capability('browserless:token', browserless_token)
        else:
            # Local development - try to find Chrome/Chromium binary
            logger.info("Using local Chrome/Chromium")
            import shutil
            chrome_binary = None
            for binary in ['chromium-browser', 'chromium', 'google-chrome', 'chrome']:
                path = shutil.which(binary)
                if path:
                    chrome_binary = path
                    logger.info(f"Found Chrome binary: {chrome_binary}")
                    break
            
            if chrome_binary:
                chrome_options.binary_location = chrome_binary
        
        # Common options for both local and Browserless
        if headless:
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--disable-gpu')
        
        # Anti-detection and performance options
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-background-timer-throttling')
        chrome_options.add_argument('--disable-backgrounding-occluded-windows')
        chrome_options.add_argument('--disable-breakpad')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-ipc-flooding-protection')
        chrome_options.add_argument('--disable-renderer-backgrounding')
        chrome_options.add_argument('--hide-scrollbars')
        chrome_options.add_argument('--mute-audio')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Realistic user agent
        chrome_options.add_argument(
            'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        # Disable images for faster loading
        prefs = {
            "profile.managed_default_content_settings.images": 2,
            "profile.default_content_setting_values.notifications": 2,
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        try:
            if browserless_endpoint:
                # Use Browserless Remote WebDriver
                self.driver = webdriver.Remote(
                    command_executor=browserless_endpoint,
                    options=chrome_options
                )
                logger.info("✅ Connected to Browserless service")
            else:
                # Try local ChromeDriver
                try:
                    self.driver = webdriver.Chrome(options=chrome_options)
                    logger.info("✅ Using local ChromeDriver")
                except Exception as e:
                    logger.debug(f"Local ChromeDriver failed: {e}")
                    
                    # Fallback to webdriver-manager
                    if WEBDRIVER_MANAGER_AVAILABLE:
                        logger.info("Trying webdriver-manager...")
                        service = Service(ChromeDriverManager().install())
                        self.driver = webdriver.Chrome(service=service, options=chrome_options)
                        logger.info("✅ Using webdriver-manager ChromeDriver")
                    else:
                        raise Exception("ChromeDriver not found. Install with: pip install webdriver-manager")
            
            # Remove webdriver property to avoid detection (if not using Browserless)
            if not browserless_endpoint:
                try:
                    self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                        'source': '''
                            Object.defineProperty(navigator, 'webdriver', {
                                get: () => undefined
                            })
                        '''
                    })
                except:
                    pass  # CDP commands might not work with Remote driver
            
            logger.info("✅ Chrome WebDriver initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            raise
    
    def verify_candidate(self, name: str, email: Optional[str] = None, 
                        phone: Optional[str] = None) -> Dict[str, Any]:
        """
        Verify candidate by searching for their LinkedIn profile on Google
        
        Args:
            name: Candidate's full name
            email: Candidate's email (optional)
            phone: Candidate's phone number (optional)
            
        Returns:
            Dictionary with verification results
        """
        if not name:
            return {
                'verified': False,
                'confidence': 0,
                'linkedin_found': False,
                'search_attempted': False,
                'error': 'No name provided'
            }
        
        try:
            # Initialize driver if not already done
            if not self.driver:
                self.initialize_driver(headless=True)
            
            # Build search query
            query_parts = [name]
            if email:
                query_parts.append(email)
            query_parts.append('LinkedIn')
            query = ' '.join(query_parts)
            
            # Perform Google search
            search_results = self._google_search(query)
            
            # Extract LinkedIn profiles from results
            linkedin_profiles = self._extract_linkedin_profiles(search_results)
            
            # Calculate confidence
            confidence = self._calculate_confidence(name, linkedin_profiles, search_results)
            
            logger.info(f"Selenium search for '{name}': Found {len(search_results)} results, {len(linkedin_profiles)} LinkedIn profiles")
            logger.info(f"LinkedIn profiles found: {linkedin_profiles}")
            
            return {
                'verified': confidence >= 60,
                'confidence': confidence,
                'linkedin_found': len(linkedin_profiles) > 0,
                'linkedin_profiles': linkedin_profiles,
                'search_attempted': True,
                'search_results_count': len(search_results),
                'search_query': query,
                'search_results_summary': [
                    {'title': r['title'], 'link': r['link']}
                    for r in search_results[:5]
                ],
                'method': 'selenium'
            }
            
        except Exception as e:
            logger.error(f"Selenium verification failed: {e}")
            return {
                'verified': False,
                'confidence': 0,
                'linkedin_found': False,
                'search_attempted': True,
                'error': str(e),
                'method': 'selenium'
            }
    
    def _google_search(self, query: str) -> List[Dict[str, str]]:
        """
        Perform search and extract results (using DuckDuckGo to avoid CAPTCHAs)
        
        Args:
            query: Search query
            
        Returns:
            List of search result dictionaries
        """
        results = []
        
        try:
            # Use Google with site:linkedin.com to get better results
            search_url = f"https://www.google.com/search?q={quote_plus(query)}+site:linkedin.com"
            
            logger.info(f"Navigating to Google: {search_url}")
            self.driver.get(search_url)
            
            # Wait for page to load
            time.sleep(3)
            
            # Wait for results
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "search"))
                )
                logger.info("✅ Found Google search results")
            except TimeoutException:
                logger.warning("⚠️ Timeout waiting for Google results")
                # Still try to parse what we have
            
            # Get HTML
            html = self.driver.page_source
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            
            # Debug: Save HTML for inspection
            try:
                with open('/tmp/google_search.html', 'w', encoding='utf-8') as f:
                    f.write(html)
                logger.info("HTML saved to /tmp/google_search.html for debugging")
            except:
                pass
            
            # Find Google search results
            # Google uses: div.g, div.tF2Cxc for organic results
            search_results = soup.select('div.g, div.tF2Cxc, div[data-sokoban-container]')
            
            logger.info(f"Found {len(search_results)} Google result containers")
            
            # FALLBACK: If no structured results, just search for LinkedIn URLs in entire HTML
            if len(search_results) == 0:
                logger.warning("No structured results found, searching entire HTML for LinkedIn URLs...")
                # Find all links
                all_links = soup.find_all('a', href=True)
                logger.info(f"Found {len(all_links)} total links in page")
                
                for link in all_links:
                    href = link.get('href', '')
                    # Clean Google redirect URLs
                    if href.startswith('/url?'):
                        # Google uses /url?q= redirect links
                        try:
                            from urllib.parse import unquote, urlparse, parse_qs
                            parsed = urlparse(href)
                            params = parse_qs(parsed.query)
                            if 'q' in params:
                                href = params['q'][0]
                        except:
                            pass
                    
                    if 'linkedin.com/in/' in href or 'linkedin.com/pub/' in href:
                        # Ensure it's a full URL
                        if not href.startswith('http'):
                            href = 'https://' + href
                        results.append({
                            'title': link.get_text(strip=True) or 'LinkedIn Profile',
                            'link': href,
                            'snippet': ''
                        })
                        logger.info(f"Found LinkedIn link: {href}")
                
                return results
            
            for idx, result in enumerate(search_results, 1):
                try:
                    # Extract title from Google result
                    title_elem = result.select_one('h3')
                    title = title_elem.get_text(strip=True) if title_elem else ''
                    
                    # Extract link from Google result
                    link_elem = result.select_one('a[href]')
                    link = link_elem.get('href', '') if link_elem else ''
                    
                    # Log original link
                    if link:
                        logger.info(f"Result {idx} original link: {link[:100]}")
                    
                    # Clean Google redirect URLs
                    if link and link.startswith('/url?'):
                        try:
                            from urllib.parse import unquote, urlparse, parse_qs
                            parsed = urlparse(link)
                            params = parse_qs(parsed.query)
                            if 'q' in params:
                                link = params['q'][0]
                                logger.info(f"Result {idx} cleaned link: {link[:100]}")
                        except Exception as e:
                            logger.warning(f"Failed to clean redirect: {e}")
                    
                    # Extract snippet
                    snippet_elem = result.select_one('[data-result="snippet"], .result__snippet')
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ''
                    
                    if title and link:
                        results.append({
                            'title': title,
                            'link': link,
                            'snippet': snippet
                        })
                        
                        # Check if it's LinkedIn
                        if 'linkedin.com' in link.lower():
                            logger.info(f"🔵 FOUND LINKEDIN: {title[:50]} | {link}")
                
                except Exception as e:
                    logger.debug(f"Error parsing search result div: {e}")
                    continue
            
            return results
            
        except Exception as e:
            logger.error(f"Google search failed: {e}")
            return []
    
    def _extract_linkedin_profiles(self, search_results: List[Dict[str, str]]) -> List[str]:
        """
        Extract LinkedIn profile URLs from search results
        
        Args:
            search_results: List of search result dictionaries
            
        Returns:
            List of LinkedIn profile URLs
        """
        linkedin_profiles = []
        
        for result in search_results:
            link = result.get('link', '')
            title = result.get('title', '')
            snippet = result.get('snippet', '')
            
            # Check if this is a LinkedIn result
            for pattern in self.linkedin_patterns:
                # Check in link
                match = re.search(pattern, link, re.IGNORECASE)
                if match:
                    profile_url = self._normalize_linkedin_url(link)
                    if profile_url and profile_url not in linkedin_profiles:
                        linkedin_profiles.append(profile_url)
                        logger.debug(f"Found LinkedIn profile in link: {profile_url}")
                
                # Also check title and snippet for LinkedIn URLs
                for text in [title, snippet]:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        # Extract the profile path
                        profile_path = match.group(0)
                        if not profile_path.startswith('http'):
                            profile_path = f"linkedin.com/{profile_path.split('linkedin.com/')[-1]}"
                        profile_url = self._normalize_linkedin_url(profile_path)
                        if profile_url and profile_url not in linkedin_profiles:
                            linkedin_profiles.append(profile_url)
                            logger.debug(f"Found LinkedIn profile in text: {profile_url}")
        
        return linkedin_profiles
    
    def _normalize_linkedin_url(self, url: str) -> str:
        """Normalize LinkedIn URL for comparison"""
        if not url:
            return ""
        
        # Convert to lowercase
        url = url.lower()
        
        # Remove protocol
        url = re.sub(r'^https?://', '', url)
        
        # Remove www.
        url = re.sub(r'^www\.', '', url)
        
        # Remove trailing slashes and query parameters
        url = url.split('?')[0].rstrip('/')
        
        # Extract just the profile path
        match = re.search(r'linkedin\.com/(in|pub)/([\w-]+)', url)
        if match:
            return f"linkedin.com/{match.group(1)}/{match.group(2)}"
        
        return url
    
    def _calculate_confidence(self, name: str, linkedin_profiles: List[str], 
                             search_results: List[Dict[str, str]]) -> int:
        """Calculate confidence score for verification"""
        score = 0
        
        # Base score if search was performed
        score += 20
        
        # LinkedIn profile found
        if linkedin_profiles:
            score += 50  # Major positive indicator
            
            # Bonus for multiple profiles
            if len(linkedin_profiles) > 1:
                score += 10
        
        # Check if search results seem relevant
        name_parts = name.lower().split()
        relevant_results = 0
        
        for result in search_results:
            text = (result.get('title', '') + ' ' + result.get('snippet', '')).lower()
            
            # Check if name parts appear in result
            if any(part in text for part in name_parts if len(part) > 2):
                relevant_results += 1
        
        # Adjust score based on relevance
        if relevant_results >= 5:
            score += 20
        elif relevant_results >= 3:
            score += 10
        
        return min(score, 100)  # Cap at 100
    
    def close(self):
        """Close the WebDriver"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("WebDriver closed")
            except Exception as e:
                logger.error(f"Error closing WebDriver: {e}")
            finally:
                self.driver = None
    
    def __del__(self):
        """Destructor to ensure WebDriver is closed"""
        self.close()
