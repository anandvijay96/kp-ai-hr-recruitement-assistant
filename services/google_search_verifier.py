"""
Google Search-based LinkedIn Profile Verifier

This service performs Google searches to verify if a candidate has a legitimate
LinkedIn profile by searching for their name, email, and phone number.
"""

import logging
import re
import requests
from typing import Dict, List, Optional, Any
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)


class GoogleSearchVerifier:
    """Verifies candidate authenticity by searching for their LinkedIn profile on Google"""
    
    def __init__(self, api_key: Optional[str] = None, search_engine_id: Optional[str] = None):
        """
        Initialize Google Search Verifier
        
        Args:
            api_key: Google Custom Search API key (optional)
            search_engine_id: Google Custom Search Engine ID (optional)
        """
        self.api_key = api_key
        self.search_engine_id = search_engine_id
        self.use_api = bool(api_key and search_engine_id)
        
        # LinkedIn URL patterns
        self.linkedin_patterns = [
            r'linkedin\.com/in/[\w-]+',
            r'linkedin\.com/pub/[\w-]+',
            r'www\.linkedin\.com/in/[\w-]+',
            r'www\.linkedin\.com/pub/[\w-]+',
        ]
    
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
            # Perform search
            if self.use_api:
                search_results = self._search_with_api(name, email, phone)
            else:
                # Fallback: Basic verification without API
                return self._basic_verification(name, email, phone)
            
            # Analyze results for LinkedIn profiles
            linkedin_profiles = self._extract_linkedin_profiles(search_results)
            
            # Calculate confidence score
            confidence = self._calculate_confidence(
                name, email, phone, linkedin_profiles, search_results
            )
            
            # Build search query for logging
            query_parts = [name]
            if email:
                query_parts.append(email)
            if phone:
                query_parts.append(phone)
            query_parts.append('LinkedIn')
            search_query = ' '.join(query_parts)
            
            # Detailed logging
            logger.info(f"Google Search performed for: {search_query}")
            logger.info(f"Found {len(search_results)} search results")
            logger.info(f"Extracted {len(linkedin_profiles)} LinkedIn profiles: {linkedin_profiles}")
            logger.info(f"Confidence: {confidence}%, Verified: {confidence >= 60}")
            
            return {
                'verified': confidence >= 60,  # 60% threshold for verification
                'confidence': confidence,
                'linkedin_found': len(linkedin_profiles) > 0,
                'linkedin_profiles': linkedin_profiles,
                'search_attempted': True,
                'search_results_count': len(search_results),
                'search_query': search_query,
                'search_results_summary': [
                    {'title': r.get('title', ''), 'link': r.get('link', '')}
                    for r in search_results[:5]  # Top 5 results
                ],
                'recommendation': self._generate_recommendation(confidence, linkedin_profiles)
            }
            
        except Exception as e:
            logger.error(f"Error during candidate verification: {e}")
            return {
                'verified': False,
                'confidence': 0,
                'linkedin_found': False,
                'search_attempted': True,
                'error': str(e),
                'recommendation': 'Unable to verify - search failed'
            }
    
    def _search_with_api(self, name: str, email: Optional[str] = None, 
                         phone: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Perform Google search using Custom Search API
        
        Args:
            name: Candidate's name
            email: Candidate's email
            phone: Candidate's phone
            
        Returns:
            List of search results
        """
        # Build search query
        query_parts = [name]
        if email:
            query_parts.append(email)
        if phone:
            # Clean phone number for search
            clean_phone = re.sub(r'[^\d+]', '', phone)
            if clean_phone:
                query_parts.append(clean_phone)
        
        query_parts.append('LinkedIn')
        query = ' '.join(query_parts)
        
        # Make API request
        url = 'https://www.googleapis.com/customsearch/v1'
        params = {
            'key': self.api_key,
            'cx': self.search_engine_id,
            'q': query,
            'num': 10  # Get top 10 results
        }
        
        try:
            logger.info(f"Making Google Search API request: {query}")
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Log response for debugging
            if 'error' in data:
                logger.error(f"Google API Error: {data['error']}")
                return []
            
            items = data.get('items', [])
            logger.info(f"Google API returned {len(items)} items")
            
            # Extract search results
            results = []
            for item in items:
                result = {
                    'title': item.get('title', ''),
                    'link': item.get('link', ''),
                    'snippet': item.get('snippet', '')
                }
                results.append(result)
                logger.debug(f"Result: {result['title'][:50]}... | {result['link']}")
            
            return results
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Google Search API request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response body: {e.response.text[:500]}")
            raise
    
    def _basic_verification(self, name: str, email: Optional[str] = None,
                           phone: Optional[str] = None) -> Dict[str, Any]:
        """
        Basic verification when API is not available
        
        This provides a fallback score based on available information
        without actually performing a search.
        """
        confidence = 50  # Neutral score when can't verify
        
        # Adjust based on information provided
        has_email = bool(email and '@' in email)
        has_phone = bool(phone and len(re.sub(r'\D', '', phone)) >= 10)
        
        if has_email:
            confidence += 10
        if has_phone:
            confidence += 10
        
        return {
            'verified': False,
            'confidence': confidence,
            'linkedin_found': False,
            'search_attempted': False,
            'recommendation': 'Google Search API not configured - unable to verify LinkedIn presence',
            'note': 'Configure GOOGLE_SEARCH_API_KEY and GOOGLE_SEARCH_ENGINE_ID to enable verification'
        }
    
    def _extract_linkedin_profiles(self, search_results: List[Dict[str, str]]) -> List[str]:
        """
        Extract LinkedIn profile URLs from search results
        
        Args:
            search_results: List of search result dictionaries
            
        Returns:
            List of LinkedIn profile URLs found
        """
        linkedin_profiles = []
        
        for result in search_results:
            link = result.get('link', '')
            title = result.get('title', '')
            snippet = result.get('snippet', '')
            
            # Check if this is a LinkedIn result
            for pattern in self.linkedin_patterns:
                # Check in link
                match = re.search(pattern, link)
                if match:
                    profile_url = match.group(0)
                    if profile_url not in linkedin_profiles:
                        linkedin_profiles.append(profile_url)
                
                # Check in title and snippet
                for text in [title, snippet]:
                    match = re.search(pattern, text)
                    if match:
                        profile_url = match.group(0)
                        if profile_url not in linkedin_profiles:
                            linkedin_profiles.append(profile_url)
        
        return linkedin_profiles
    
    def _calculate_confidence(self, name: str, email: Optional[str], phone: Optional[str],
                             linkedin_profiles: List[str], 
                             search_results: List[Dict[str, str]]) -> int:
        """
        Calculate confidence score for candidate verification
        
        Args:
            name: Candidate name
            email: Candidate email
            phone: Candidate phone
            linkedin_profiles: Found LinkedIn profiles
            search_results: All search results
            
        Returns:
            Confidence score (0-100)
        """
        score = 0
        
        # Base score if search was performed
        score += 20
        
        # LinkedIn profile found
        if linkedin_profiles:
            score += 40  # Major positive indicator
            
            # Bonus if multiple profiles found (common for popular names)
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
        elif relevant_results >= 1:
            score += 5
        
        # Penalty if no results found
        if not search_results:
            score = max(score - 30, 0)
        
        return min(score, 100)  # Cap at 100
    
    def _generate_recommendation(self, confidence: int, 
                                 linkedin_profiles: List[str]) -> str:
        """
        Generate human-readable recommendation based on verification results
        
        Args:
            confidence: Confidence score
            linkedin_profiles: Found LinkedIn profiles
            
        Returns:
            Recommendation string
        """
        if confidence >= 80:
            if len(linkedin_profiles) > 1:
                return f"✓ Strong verification - {len(linkedin_profiles)} LinkedIn profiles found"
            elif len(linkedin_profiles) == 1:
                return "✓ Strong verification - LinkedIn profile found"
            else:
                return "✓ Good verification - strong online presence"
        
        elif confidence >= 60:
            if linkedin_profiles:
                return "○ Moderate verification - LinkedIn profile found"
            else:
                return "○ Moderate verification - some online presence"
        
        else:
            if not linkedin_profiles:
                return "✗ Weak verification - No LinkedIn profile found"
            else:
                return "○ Weak verification - limited online presence"
    
    def format_for_display(self, verification_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format verification results for UI display
        
        Args:
            verification_result: Raw verification results
            
        Returns:
            Formatted results for display
        """
        if not verification_result.get('search_attempted'):
            return {
                'status': 'not_verified',
                'badge_color': 'secondary',
                'icon': '⚠️',
                'message': verification_result.get('recommendation', 'Not verified'),
                'details': verification_result.get('note', '')
            }
        
        confidence = verification_result.get('confidence', 0)
        linkedin_found = verification_result.get('linkedin_found', False)
        
        if confidence >= 80:
            status = 'verified'
            badge_color = 'success'
            icon = '✓'
        elif confidence >= 60:
            status = 'partially_verified'
            badge_color = 'warning'
            icon = '○'
        else:
            status = 'not_verified'
            badge_color = 'danger'
            icon = '✗'
        
        details = []
        if linkedin_found:
            profiles = verification_result.get('linkedin_profiles', [])
            details.append(f"LinkedIn profiles found: {len(profiles)}")
        else:
            details.append("No LinkedIn profile found in search results")
        
        return {
            'status': status,
            'badge_color': badge_color,
            'icon': icon,
            'confidence': confidence,
            'message': verification_result.get('recommendation', ''),
            'details': ' | '.join(details),
            'linkedin_profiles': verification_result.get('linkedin_profiles', [])
        }
