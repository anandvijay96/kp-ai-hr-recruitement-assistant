"""
Resume Authenticity Analyzer
"""
import re
from typing import Dict, Any, List, Optional
from collections import Counter
import logging

from services.google_search_verifier import GoogleSearchVerifier
from services.selenium_linkedin_verifier import SeleniumLinkedInVerifier

logger = logging.getLogger(__name__)

class ResumeAuthenticityAnalyzer:
    """Analyzes resume authenticity using multiple criteria"""

    def __init__(self, google_search_verifier=None, use_selenium=True):
        """
        Initialize Resume Authenticity Analyzer
        
        Args:
            google_search_verifier: Optional GoogleSearchVerifier instance for LinkedIn verification
            use_selenium: Use Selenium for more accurate Google searches (default: True)
        """
        self.google_search_verifier = google_search_verifier
        self.use_selenium = use_selenium
        self.selenium_verifier = None
        
        # Initialize Selenium verifier if requested
        if use_selenium:
            try:
                self.selenium_verifier = SeleniumLinkedInVerifier()
                logger.info("✅ Selenium LinkedIn verifier initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Selenium verifier: {e}")
                logger.info("Falling back to Google API verification")
        
        try:
            import nltk
            # Download required NLTK data if not available
            for resource in ['punkt', 'punkt_tab']:
                try:
                    nltk.data.find(f'tokenizers/{resource}')
                except (LookupError, OSError):
                    try:
                        nltk.download(resource, quiet=True)
                    except Exception as e:
                        logger.warning(f"Could not download NLTK {resource}: {e}")
        except ImportError:
            logger.warning("NLTK not available for grammar analysis")

    def analyze_authenticity(self, text_content: str, structure_info: Dict[str, Any],
                           candidate_name: Optional[str] = None,
                           candidate_email: Optional[str] = None,
                           candidate_phone: Optional[str] = None) -> Dict[str, Any]:
        """Analyze resume authenticity using multiple criteria"""

        # Check LinkedIn profile (in resume and via Google search)
        try:
            linkedin_check_result = self._check_linkedin_profile(
                text_content, candidate_name, candidate_email, candidate_phone
            )
            # Safety check
            if linkedin_check_result is None:
                logger.warning("LinkedIn check returned None, using default")
                linkedin_check_result = {
                    'score': 50.0,
                    'found_in_resume': False,
                    'google_verification': None,
                    'cross_verified': False
                }
        except Exception as e:
            logger.error(f"LinkedIn profile check failed: {str(e)}")
            linkedin_check_result = {
                'score': 50.0,
                'found_in_resume': False,
                'google_verification': None,
                'cross_verified': False
            }
        
        scores = {
            'font_consistency': self._analyze_font_consistency(structure_info),
            'grammar_quality': self._analyze_grammar_quality(text_content),
            'formatting_consistency': self._analyze_formatting_consistency(structure_info),
            'content_suspicious_patterns': self._analyze_suspicious_patterns(text_content),
            'structure_consistency': self._analyze_structure_consistency(structure_info),
            'linkedin_profile': linkedin_check_result['score'],
            'capitalization_consistency': self._analyze_capitalization_consistency(text_content)
        }

        # Calculate overall score (weighted average)
        # LinkedIn is CRITICAL in modern hiring - given highest weight
        weights = {
            'font_consistency': 0.15,
            'grammar_quality': 0.15,
            'formatting_consistency': 0.10,
            'content_suspicious_patterns': 0.08,
            'structure_consistency': 0.07,
            'linkedin_profile': 0.35,  # CRITICAL: 35% weight for LinkedIn presence
            'capitalization_consistency': 0.10
        }

        overall_score = sum(scores[criteria] * weights[criteria] for criteria in scores)
        
        # Apply additional penalty if LinkedIn is critically low (< 30%)
        # This ensures missing LinkedIn significantly impacts the score
        if scores['linkedin_profile'] < 30:
            # Apply 10-20% penalty based on how low the LinkedIn score is
            penalty = (30 - scores['linkedin_profile']) / 30 * 0.20  # Up to 20% penalty
            overall_score = overall_score * (1 - penalty)

        # Generate flags and warnings
        flags = self._generate_flags(scores, text_content, linkedin_check_result)

        # Generate detailed diagnostics
        diagnostics = self._generate_detailed_diagnostics(
            text_content, structure_info, scores, linkedin_check_result
        )

        return {
            'overall_score': round(overall_score, 1),
            'font_consistency': round(scores['font_consistency'], 1),
            'grammar_score': round(scores['grammar_quality'], 1),
            'formatting_score': round(scores['formatting_consistency'], 1),
            'visual_consistency': round(scores['structure_consistency'], 1),
            'linkedin_profile_score': round(scores['linkedin_profile'], 1),
            'capitalization_score': round(scores['capitalization_consistency'], 1),
            'details': self._generate_analysis_details(scores, text_content),
            'flags': flags,
            'diagnostics': diagnostics
        }

    def _analyze_font_consistency(self, structure_info: Dict[str, Any]) -> float:
        """Analyze font consistency across the document"""
        try:
            font_analysis = structure_info.get('font_analysis', {})
            unique_fonts = font_analysis.get('unique_fonts', 0)

            # Fewer fonts = more consistent = higher score
            if unique_fonts <= 2:
                return 95.0
            elif unique_fonts <= 4:
                return 85.0
            elif unique_fonts <= 6:
                return 70.0
            else:
                return 50.0
        except Exception as e:
            logger.error(f"Font consistency analysis failed: {str(e)}")
            return 75.0  # Default moderate score

    def _analyze_grammar_quality(self, text_content: str) -> float:
        """Analyze grammar quality and language patterns"""
        try:
            import nltk
            from nltk.tokenize import sent_tokenize, word_tokenize

            sentences = sent_tokenize(text_content)
            words = word_tokenize(text_content)

            if not sentences or not words:
                return 50.0

            # Check for common grammar issues
            grammar_issues = 0

            # Check sentence length consistency
            sentence_lengths = [len(word_tokenize(sent)) for sent in sentences]
            avg_length = sum(sentence_lengths) / len(sentence_lengths)

            # Flag very short or very long sentences
            for length in sentence_lengths:
                if length < 3 or length > 50:
                    grammar_issues += 1

            # Check for excessive capitalization (SCREAMING TEXT)
            capitalized_words = sum(1 for word in words if word.isupper() and len(word) > 3)
            if capitalized_words > len(words) * 0.1:  # More than 10% capitalized
                grammar_issues += 2

            # Check for excessive punctuation
            punctuation_count = sum(1 for char in text_content if char in '!@#$%^&*()')
            if punctuation_count > len(text_content) * 0.05:  # More than 5% punctuation
                grammar_issues += 1

            # Calculate score (inverse of issues)
            max_issues = len(sentences) * 0.3  # Allow 30% of sentences to have issues
            issue_penalty = min(grammar_issues / max(max_issues, 1), 1.0)

            return max(0, 100 - (issue_penalty * 50))

        except ImportError:
            # Fallback if NLTK not available
            return self._basic_grammar_check(text_content)
        except Exception as e:
            logger.error(f"Grammar analysis failed: {str(e)}")
            return 75.0

    def _basic_grammar_check(self, text_content: str) -> float:
        """Basic grammar check without NLTK"""
        issues = 0

        # Check for excessive exclamation marks
        if text_content.count('!') > text_content.count('.') * 2:
            issues += 2

        # Check for excessive capitalization
        words = text_content.split()
        capitalized_words = sum(1 for word in words if word.isupper() and len(word) > 3)
        if capitalized_words > len(words) * 0.15:
            issues += 2

        # Check for very short sentences (fragmented text)
        sentences = [s.strip() for s in text_content.split('.') if s.strip()]
        short_sentences = sum(1 for s in sentences if len(s.split()) < 3)
        if short_sentences > len(sentences) * 0.3:
            issues += 1

        return max(0, 100 - (issues * 15))

    def _analyze_formatting_consistency(self, structure_info: Dict[str, Any]) -> float:
        """Analyze formatting consistency"""
        try:
            layout_analysis = structure_info.get('layout_analysis', {})

            # Check if fonts are consistent across pages
            consistent_fonts = layout_analysis.get('consistent_fonts', True)

            # Check page count (too many pages might indicate template stuffing)
            page_count = structure_info.get('page_count', 1)
            if page_count > 10:
                return 60.0  # Suspiciously long resume
            elif page_count > 5:
                return 80.0
            else:
                return 90.0 if consistent_fonts else 70.0

        except Exception as e:
            logger.error(f"Formatting analysis failed: {str(e)}")
            return 75.0

    def _analyze_suspicious_patterns(self, text_content: str) -> float:
        """Look for patterns commonly found in fake resumes"""
        suspicious_indicators = 0
        total_indicators = 5

        # 1. Check for template-like repeated phrases
        repeated_phrases = self._find_repeated_phrases(text_content)
        if repeated_phrases > 3:
            suspicious_indicators += 1

        # 2. Check for placeholder text patterns
        placeholder_patterns = [
            r'\b(lorem ipsum|placeholder|sample text)\b',
            r'\b(experience|skill|achievement)\s+\d+\b',
            r'\b(placeholder|template|example)\b'
        ]

        for pattern in placeholder_patterns:
            if re.search(pattern, text_content, re.IGNORECASE):
                suspicious_indicators += 1

        # 3. Check for generic job titles
        generic_titles = [
            'software engineer', 'developer', 'manager', 'analyst', 'specialist'
        ]

        title_matches = sum(1 for title in generic_titles
                          if title.lower() in text_content.lower())
        if title_matches > 3:
            suspicious_indicators += 1

        # 4. Check for inconsistent date formats
        date_patterns = [
            r'\b\d{1,2}/\d{1,2}/\d{4}\b',  # MM/DD/YYYY
            r'\b\d{1,2}-\d{1,2}-\d{4}\b',  # MM-DD-YYYY
            r'\b\d{4}-\d{1,2}-\d{1,2}\b',  # YYYY-MM-DD
        ]

        date_formats_found = []
        for pattern in date_patterns:
            matches = re.findall(pattern, text_content)
            if matches:
                date_formats_found.append(pattern)

        if len(date_formats_found) > 1:
            suspicious_indicators += 1

        # 5. Check for excessive bullet points (template-like structure)
        bullet_lines = text_content.count('•') + text_content.count('●') + text_content.count('■')
        total_lines = len([line for line in text_content.split('\n') if line.strip()])
        if total_lines > 0 and (bullet_lines / total_lines) > 0.7:
            suspicious_indicators += 1

        # Calculate score (inverse of suspicious indicators)
        return max(0, 100 - (suspicious_indicators / total_indicators * 100))

    def _find_repeated_phrases(self, text_content: str) -> int:
        """Find repeated phrases that might indicate template usage"""
        words = text_content.lower().split()
        if len(words) < 10:
            return 0

        # Look for repeated 3-word phrases
        phrases = [' '.join(words[i:i+3]) for i in range(len(words)-2)]
        phrase_counts = Counter(phrases)

        # Count phrases that appear more than twice
        repeated_count = sum(1 for count in phrase_counts.values() if count > 2)
        return min(repeated_count, 10)  # Cap at 10

    def _analyze_structure_consistency(self, structure_info: Dict[str, Any]) -> float:
        """Analyze overall document structure consistency"""
        try:
            # If we have page information, check consistency across pages
            pages_info = structure_info.get('font_analysis', {}).get('pages_info', [])

            if not pages_info:
                return 75.0  # Default if no page info available

            # Check if text length is consistent across pages
            text_lengths = [page.get('text_length', 0) for page in pages_info]

            if not text_lengths:
                return 75.0

            avg_length = sum(text_lengths) / len(text_lengths)
            variance = sum((length - avg_length) ** 2 for length in text_lengths) / len(text_lengths)

            # High variance might indicate inconsistent formatting
            if variance > avg_length * 0.5:
                return 60.0
            else:
                return 90.0

        except Exception as e:
            logger.error(f"Structure analysis failed: {str(e)}")
            return 75.0

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
        
        # Remove trailing slashes
        url = url.rstrip('/')
        
        # Extract just the profile path (e.g., linkedin.com/in/username)
        match = re.search(r'linkedin\.com/(in|pub)/([\w-]+)', url)
        if match:
            return f"linkedin.com/{match.group(1)}/{match.group(2)}"
        
        return url
    
    def _check_linkedin_profile(self, text_content: str, 
                               candidate_name: Optional[str] = None,
                               candidate_email: Optional[str] = None,
                               candidate_phone: Optional[str] = None) -> Dict[str, Any]:
        """
        Check for LinkedIn profile URL in resume and ALWAYS verify via Google search
        Google verification is mandatory for proper scoring regardless of resume content.
        
        Returns:
            Dictionary with score and verification details
        """
        try:
            result = {
                'score': 0.0,
                'found_in_resume': False,
                'google_verification': None,
                'linkedin_url': None,
                'other_profiles': [],
                'cross_verified': False
            }
            
            # LinkedIn URL patterns
            linkedin_patterns = [
                r'linkedin\.com/in/[\w-]+',
                r'www\.linkedin\.com/in/[\w-]+',
                r'in\.linkedin\.com/in/[\w-]+',
                r'linkedin\.com/pub/[\w-]+'
            ]

            # Check for LinkedIn in resume
            for pattern in linkedin_patterns:
                match = re.search(pattern, text_content, re.IGNORECASE)
                if match:
                    result['found_in_resume'] = True
                    result['linkedin_url'] = match.group(0)
                    break

            # Check for other professional profiles as partial credit
            other_profiles = [
                (r'github\.com/[\w-]+', 'GitHub'),
                (r'gitlab\.com/[\w-]+', 'GitLab'),
                (r'stackoverflow\.com/users/[\w-]+', 'StackOverflow'),
                (r'medium\.com/@[\w-]+', 'Medium')
            ]

            for pattern, platform in other_profiles:
                match = re.search(pattern, text_content, re.IGNORECASE)
                if match:
                    result['other_profiles'].append({
                        'platform': platform,
                        'url': match.group(0)
                    })

            # ALWAYS perform Google verification if configured and we have candidate info
            # Priority: Selenium (more accurate) > API (limited)
            verification = None
            if candidate_name:
                # Try Selenium first (more accurate, real browser results)
                if self.selenium_verifier:
                    try:
                        logger.info(f"Using Selenium for LinkedIn verification: {candidate_name}")
                        verification = self.selenium_verifier.verify_candidate(
                            candidate_name, candidate_email, candidate_phone
                        )
                        logger.info(f"✅ Selenium verification complete")
                    except Exception as e:
                        logger.warning(f"Selenium verification failed: {e}, falling back to API")
                        verification = None
                
                # Fallback to API if Selenium failed or not available
                if not verification and self.google_search_verifier:
                    try:
                        logger.info("Using Google API for LinkedIn verification")
                        verification = self.google_search_verifier.verify_candidate(
                            candidate_name, candidate_email, candidate_phone
                        )
                    except Exception as e:
                        logger.warning(f"API verification also failed: {e}")
                        verification = None
            
            if verification:
                result['google_verification'] = verification
                
                # NEW SCORING LOGIC: Cross-verification with flexible matching
                # Check if the LinkedIn URL from resume matches any found by Google
                linkedin_matches = False
                linkedin_found_online = verification.get('linkedin_found', False)
                
                if result['found_in_resume'] and result['linkedin_url'] and linkedin_found_online:
                    resume_linkedin = self._normalize_linkedin_url(result['linkedin_url'])
                    google_linkedins = verification.get('linkedin_profiles', [])
                    
                    # Try exact match first
                    for google_profile in google_linkedins:
                        normalized_google = self._normalize_linkedin_url(google_profile)
                        if resume_linkedin == normalized_google:
                            linkedin_matches = True
                            logger.info(f"✅ LinkedIn cross-verified (exact): {result['linkedin_url']} matches {google_profile}")
                            break
                    
                    # If no exact match but Google found LinkedIn profiles, give benefit of doubt
                    # Google CSE API has indexing limitations - if ANY LinkedIn found, it's promising
                    if not linkedin_matches and len(google_linkedins) > 0:
                        logger.info(f"⚠️ No exact match, but Google found {len(google_linkedins)} LinkedIn profiles")
                        logger.info(f"   Resume: {result['linkedin_url']}")
                        logger.info(f"   Google: {google_linkedins}")
                        # Partial credit - person likely exists, just API indexing issue
                        linkedin_matches = "partial"
                
                # Scoring based on verification results
                if result['found_in_resume'] and linkedin_matches == True:
                    # BEST CASE: LinkedIn in resume AND exact match on Google
                    result['score'] = 100.0
                    result['cross_verified'] = True
                elif result['found_in_resume'] and linkedin_matches == "partial":
                    # GOOD: LinkedIn in resume AND Google found LinkedIn results (but not exact)
                    # Give benefit of doubt - likely valid but API indexing limitations
                    result['score'] = 85.0
                    result['cross_verified'] = True  # Mark as verified (API limitations)
                    logger.info("✅ LinkedIn verified (API indexing limitation)")
                elif result['found_in_resume'] and linkedin_found_online and not linkedin_matches:
                    # CAUTION: LinkedIn in resume, Google found OTHER LinkedIn profiles
                    # Could be legitimate (common name) or suspicious
                    result['score'] = 70.0
                    result['cross_verified'] = False
                elif result['found_in_resume'] and not linkedin_found_online:
                    # SUSPICIOUS: LinkedIn in resume but Google found NO LinkedIn at all
                    result['score'] = 50.0
                    result['cross_verified'] = False
                elif not result['found_in_resume'] and verification.get('linkedin_found'):
                    # GOOD: LinkedIn verified on Google but not in resume
                    result['score'] = 75.0
                    result['cross_verified'] = True
                elif verification.get('verified'):
                    # FAIR: Verified online presence but no LinkedIn
                    result['score'] = 60.0 if result['other_profiles'] else 40.0
                elif verification.get('search_attempted'):
                    # POOR: Search attempted but no strong verification
                    result['score'] = 20.0
            else:
                # No Google verification available (API not configured)
                if result['found_in_resume']:
                    # LinkedIn in resume but can't cross-verify
                    result['score'] = 70.0  # Reduced score - can't verify authenticity
                elif result['other_profiles']:
                    result['score'] = 50.0
                else:
                    result['score'] = 0.0

            return result

        except Exception as e:
            logger.error(f"LinkedIn profile check failed: {str(e)}")
            return {
                'score': 50.0,  # Default neutral score
                'found_in_resume': False,
                'google_verification': None,
                'cross_verified': False,
                'error': str(e)
            }

    def _analyze_capitalization_consistency(self, text_content: str) -> float:
        """Analyze capitalization consistency across the document"""
        try:
            words = text_content.split()
            if len(words) < 10:
                return 75.0  # Not enough text to analyze

            issues = 0
            total_checks = 0

            # 1. Check for random mid-word capitals (e.g., "aCcOuNt")
            for word in words:
                if len(word) > 3 and word.isalpha():
                    total_checks += 1
                    # Check if word has mixed case in unusual patterns
                    if word[0].islower() and any(c.isupper() for c in word[1:]):
                        # Exclude common patterns like "iPhone", "eBay"
                        if not word.startswith(('i', 'e')) or len(word) < 5:
                            issues += 1
                    # Check for alternating case
                    elif sum(1 for i in range(len(word)-1) if word[i].islower() != word[i+1].islower()) > len(word) * 0.5:
                        issues += 1

            # 2. Check for inconsistent skill capitalization
            common_skills = [
                'python', 'java', 'javascript', 'react', 'angular', 'node',
                'sql', 'aws', 'azure', 'docker', 'kubernetes', 'git'
            ]

            skill_variations = {}
            for skill in common_skills:
                variations = set()
                for word in words:
                    if word.lower() == skill:
                        variations.add(word)
                if len(variations) > 1:
                    skill_variations[skill] = variations
                    issues += 1

            # 3. Check for sentence case violations
            sentences = [s.strip() for s in text_content.split('.') if s.strip()]
            for sentence in sentences:
                if sentence and len(sentence) > 10:  
                    # Skip bullet points and list markers
                    if sentence.startswith(('•', '-', '*', '○', '●', '■', '□')):
                        continue
                    
                    # Skip if it's an email, URL, or technical string
                    if '@' in sentence[:20] or 'http' in sentence[:20].lower() or 'www.' in sentence[:20].lower():
                        continue
                    if '/' in sentence[:15] or '.com' in sentence[:20] or '.in' in sentence[:20]:
                        continue
                    
                    # Check if first character is lowercase
                    total_checks += 1
                    # Check if sentence starts with lowercase (excluding bullet points and list markers)
                    first_word = sentence.split()[0] if sentence.split() else ""
                    if first_word and first_word[0].islower() and not sentence.startswith(('•', '-', '*', '○', '●', '■', '□')):
                        # Additional check: Skip if it's likely a continuation or code snippet
                        if len(first_word) > 2 and first_word.isalpha():
                            issues += 1

            # Calculate score
            if total_checks == 0:
                return 75.0

            issue_ratio = issues / total_checks
            score = max(0, 100 - (issue_ratio * 100))

            return score

        except Exception as e:
            logger.error(f"Capitalization analysis failed: {str(e)}")
            return 75.0

    def _generate_flags(self, scores: Dict[str, float], text_content: str,
                       linkedin_check_result: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate warning flags based on analysis"""
        flags = []

        # Safety check for linkedin_check_result
        if linkedin_check_result is None:
            logger.warning("linkedin_check_result is None in _generate_flags, using defaults")
            linkedin_check_result = {
                'found_in_resume': False,
                'google_verification': None,
                'cross_verified': False
            }

        # LinkedIn profile flag (enhanced with mandatory Google cross-verification)
        found_in_resume = linkedin_check_result.get('found_in_resume', False)
        google_verification = linkedin_check_result.get('google_verification') or {}
        google_verified = google_verification.get('linkedin_found', False)
        cross_verified = linkedin_check_result.get('cross_verified', False)
        search_attempted = google_verification.get('search_attempted', False)
        
        if found_in_resume and cross_verified:
            # BEST CASE: LinkedIn in resume AND verified online - no flag needed
            pass
        elif found_in_resume and search_attempted and not google_verified:
            # SUSPICIOUS: LinkedIn in resume but NOT found on Google
            flags.append({
                'type': 'warning',
                'category': 'Professional Profile',
                'message': '⚠️ LinkedIn URL in resume could not be verified on Google - possible fake profile',
                'severity': 'high'
            })
        elif found_in_resume and not search_attempted:
            # LinkedIn in resume but couldn't verify (API not configured)
            flags.append({
                'type': 'info',
                'category': 'Professional Profile',
                'message': 'LinkedIn URL in resume (not cross-verified - Google API not configured)',
                'severity': 'medium'
            })
        elif not found_in_resume and google_verified:
            # LinkedIn verified online but not in resume
            flags.append({
                'type': 'info',
                'category': 'Professional Profile',
                'message': '✓ LinkedIn profile verified via Google search (not in resume - suggest adding)',
                'severity': 'low'
            })
        elif linkedin_check_result.get('other_profiles'):
            # Only alternative profiles found
            profiles = linkedin_check_result.get('other_profiles', [])
            platforms = ', '.join([p['platform'] for p in profiles])
            flags.append({
                'type': 'info',
                'category': 'Professional Profile',
                'message': f'Alternative professional profiles found: {platforms}',
                'severity': 'low'
            })
        elif scores['linkedin_profile'] == 0 or scores['linkedin_profile'] <= 20:
            # No profile found anywhere
            flags.append({
                'type': 'warning',
                'category': 'Professional Profile',
                'message': '❌ No LinkedIn profile found (in resume or online)',
                'severity': 'high'
            })

        # Capitalization consistency flag
        if scores['capitalization_consistency'] < 60:
            flags.append({
                'type': 'warning',
                'category': 'Formatting',
                'message': 'Inconsistent capitalization detected',
                'severity': 'medium'
            })

        # Grammar quality flag
        if scores['grammar_quality'] < 60:
            flags.append({
                'type': 'warning',
                'category': 'Content Quality',
                'message': 'Grammar issues detected',
                'severity': 'medium'
            })

        # Font consistency flag
        if scores['font_consistency'] < 70:
            flags.append({
                'type': 'warning',
                'category': 'Visual Consistency',
                'message': 'Multiple font types detected',
                'severity': 'low'
            })

        # Suspicious patterns flag
        if scores['content_suspicious_patterns'] < 70:
            flags.append({
                'type': 'warning',
                'category': 'Content Authenticity',
                'message': 'Potential template usage detected',
                'severity': 'high'
            })

        return flags

    def _generate_analysis_details(self, scores: Dict[str, float], text_content: str) -> List[str]:
        """Generate detailed analysis feedback"""
        details = []

        if scores['font_consistency'] < 70:
            details.append("Multiple font types detected - consider standardizing fonts")
        elif scores['font_consistency'] > 90:
            details.append("Font usage is consistent across the document")

        if scores['grammar_quality'] < 60:
            details.append("Grammar issues detected - review for typos and sentence structure")
        elif scores['grammar_quality'] > 85:
            details.append("Good grammar and language quality")

        if scores['content_suspicious_patterns'] < 70:
            details.append("Some content patterns may indicate template usage")
        elif scores['content_suspicious_patterns'] > 85:
            details.append("Content appears original and authentic")

        if scores['linkedin_profile'] == 0:
            details.append("No LinkedIn profile found - consider adding professional profile")
        elif scores['linkedin_profile'] == 100:
            details.append("LinkedIn profile found")

        if scores['capitalization_consistency'] < 70:
            details.append("Inconsistent capitalization detected - review formatting")
        elif scores['capitalization_consistency'] > 85:
            details.append("Capitalization is consistent throughout the document")

        if not details:
            details.append("Document structure analysis completed - no significant issues found")

        return details

    def _generate_detailed_diagnostics(self, text_content: str, structure_info: Dict[str, Any], 
                                      scores: Dict[str, float],
                                      linkedin_check_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate detailed diagnostics for each criterion"""
        diagnostics = {}

        # 1. Font Usage Diagnostics
        diagnostics['fonts'] = self._get_font_diagnostics(structure_info)

        # 2. Capitalization Issues Diagnostics
        diagnostics['capitalization'] = self._get_capitalization_diagnostics(text_content)

        # 3. LinkedIn Profile Diagnostics (enhanced with Google verification)
        diagnostics['linkedin'] = self._get_linkedin_diagnostics(text_content, linkedin_check_result)

        # 4. Grammar Issues Diagnostics
        diagnostics['grammar'] = self._get_grammar_diagnostics(text_content)

        return diagnostics

    def _get_font_diagnostics(self, structure_info: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed font usage information"""
        try:
            font_analysis = structure_info.get('font_analysis', {})
            
            # Get font details
            font_list = font_analysis.get('font_list', [])
            font_families = font_analysis.get('font_families', [])
            unique_fonts = font_analysis.get('unique_fonts', 0)
            
            # Parse font information and group by family
            font_breakdown = {}
            
            # If we have font_families, use them (better approach)
            if font_families:
                # Group font variants by family
                family_variants = {}
                for font_info in font_list:
                    try:
                        if ':' in font_info:
                            font_name = font_info.split(':')[0]
                            # Normalize to get family
                            from document_processor import DocumentProcessor
                            processor = DocumentProcessor()
                            family = processor._normalize_font_family(font_name)
                            
                            if family not in family_variants:
                                family_variants[family] = []
                            if font_name not in family_variants[family]:
                                family_variants[family].append(font_name)
                    except Exception:
                        continue
                
                # Create breakdown showing families
                for family in font_families:
                    variants = family_variants.get(family, [])
                    count = len(variants) if variants else 1
                    font_breakdown[family] = f"{count} times" if count > 1 else "1 time"
            
            # Fallback: old logic
            elif font_list:
                for font_info in font_list:
                    try:
                        if ':' in font_info:
                            font_name = font_info.split(':')[0]
                            if font_name in font_breakdown:
                                font_breakdown[font_name] += 1
                            else:
                                font_breakdown[font_name] = 1
                    except Exception:
                        continue
            
            # Fallback if still no data
            if not font_breakdown:
                font_breakdown = {'info': 'Font details not available'}
            
            return {
                'total_unique_fonts': unique_fonts,
                'fonts_breakdown': font_breakdown,
                'font_list': font_list[:10] if font_list else [],  # Show first 10 for reference
                'recommendation': self._get_font_recommendation(unique_fonts)
            }
        except Exception as e:
            logger.error(f"Font diagnostics failed: {str(e)}")
            return {
                'total_unique_fonts': 0,
                'fonts_breakdown': {'info': 'Font analysis not available'},
                'font_list': [],
                'recommendation': 'Unable to analyze fonts'
            }

    def _get_font_recommendation(self, unique_fonts: int) -> str:
        """Get recommendation based on font count"""
        if unique_fonts <= 2:
            return "✅ Excellent - Font usage is consistent"
        elif unique_fonts <= 4:
            return "⚠️ Good - Consider reducing to 2-3 fonts for better consistency"
        elif unique_fonts <= 6:
            return "⚠️ Fair - Too many fonts detected. Standardize to 2-3 fonts"
        else:
            return "❌ Poor - Excessive font variety. Use maximum 2-3 fonts throughout"

    def _get_capitalization_diagnostics(self, text_content: str) -> Dict[str, Any]:
        """Get detailed capitalization issues"""
        try:
            words = text_content.split()
            issues = []
            
            # Find specific capitalization issues
            # 1. Random mid-word capitals
            random_caps = []
            for word in words[:200]:  # Check first 200 words for performance
                if len(word) > 3 and word.isalpha():
                    if word[0].islower() and any(c.isupper() for c in word[1:]):
                        if not word.startswith(('i', 'e')) or len(word) < 5:
                            random_caps.append(word)
            
            if random_caps:
                issues.append({
                    'type': 'Random Capitalization',
                    'severity': 'high',
                    'examples': random_caps[:5],  # Show first 5 examples
                    'count': len(random_caps),
                    'fix': 'Use consistent capitalization (e.g., "Software" not "SoFtWaRe")'
                })
            
            # 2. Inconsistent skill capitalization
            common_skills = ['python', 'java', 'javascript', 'react', 'angular', 'node', 'sql', 'aws', 'azure', 'docker', 'kubernetes', 'git']
            skill_variations = {}
            
            for skill in common_skills:
                variations = set()
                for word in words:
                    if word.lower() == skill:
                        variations.add(word)
                if len(variations) > 1:
                    skill_variations[skill] = list(variations)
            
            if skill_variations:
                issues.append({
                    'type': 'Inconsistent Skill Capitalization',
                    'severity': 'medium',
                    'examples': skill_variations,
                    'count': len(skill_variations),
                    'fix': 'Use consistent capitalization for skills (e.g., always "Python" or always "python")'
                })
            
            # 3. Sentence case violations
            sentences = [s.strip() for s in text_content.split('.') if s.strip()]
            lowercase_starts = []
            
            for sentence in sentences[:20]:  # Check first 20 sentences
                if sentence and len(sentence) > 5:
                    # Skip if starts with bullet points
                    if sentence.startswith(('•', '-', '*')):
                        continue
                    # Skip if it's an email, URL, or technical string
                    if '@' in sentence[:20] or 'http' in sentence[:20].lower() or 'www.' in sentence[:20].lower():
                        continue
                    if '/' in sentence[:15] or '.com' in sentence[:20] or '.in' in sentence[:20]:
                        continue
                    # Check for sentence case violation
                    if sentence[0].islower():
                        lowercase_starts.append(sentence[:50] + '...' if len(sentence) > 50 else sentence)
            
            if lowercase_starts:
                issues.append({
                    'type': 'Sentence Case Violations',
                    'severity': 'low',
                    'examples': lowercase_starts[:3],
                    'count': len(lowercase_starts),
                    'fix': 'Start sentences with capital letters'
                })
            
            return {
                'issues_found': len(issues),
                'details': issues if issues else [{'type': 'No Issues', 'message': '✅ Capitalization is consistent'}]
            }
            
        except Exception as e:
            logger.error(f"Capitalization diagnostics failed: {str(e)}")
            return {
                'issues_found': 0,
                'details': [{'type': 'Error', 'message': 'Unable to analyze capitalization'}]
            }

    def _get_linkedin_diagnostics(self, text_content: str, 
                                  linkedin_check_result: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed LinkedIn profile search results with mandatory Google cross-verification"""
        try:
            # Safety check for linkedin_check_result
            if linkedin_check_result is None:
                logger.warning("linkedin_check_result is None in _get_linkedin_diagnostics")
                return {
                    'status': 'error',
                    'profile': None,
                    'alternatives': [],
                    'recommendation': 'Unable to analyze professional profiles'
                }
            
            found_in_resume = linkedin_check_result.get('found_in_resume', False)
            linkedin_url = linkedin_check_result.get('linkedin_url')
            other_profiles = linkedin_check_result.get('other_profiles', [])
            google_verification = linkedin_check_result.get('google_verification')
            cross_verified = linkedin_check_result.get('cross_verified', False)
            
            # Build LinkedIn profile info if found in resume
            linkedin_found = None
            if found_in_resume and linkedin_url:
                # Extract username from URL
                username_match = re.search(r'linkedin\.com/(?:in|pub)/([\w-]+)', linkedin_url, re.IGNORECASE)
                username = username_match.group(1) if username_match else 'Unknown'
                
                # Determine status based on cross-verification
                if cross_verified:
                    status = '✅ Found in Resume & Verified Online'
                elif google_verification and google_verification.get('search_attempted'):
                    status = '⚠️ Found in Resume but NOT Verified Online'
                else:
                    status = '⚠️ Found in Resume (Not Cross-Verified)'
                
                linkedin_found = {
                    'type': 'LinkedIn',
                    'url': linkedin_url,
                    'username': username,
                    'status': status,
                    'cross_verified': cross_verified
                }
            
            # Check Google verification results if available
            google_verified_linkedin = None
            if google_verification and google_verification.get('linkedin_found'):
                profiles = google_verification.get('linkedin_profiles', [])
                if profiles:
                    google_verified_linkedin = {
                        'profiles': profiles,
                        'confidence': google_verification.get('confidence', 0),
                        'status': '✅ Verified via Google Search'
                    }
            
            # Determine final status and recommendation based on cross-verification
            if linkedin_found and cross_verified:
                # Extract verification details
                verification_details = {}
                if google_verification:
                    search_query = google_verification.get('search_query', '')
                    method = google_verification.get('method', 'unknown')
                    search_url = None
                    
                    # Generate search URL based on method
                    if method == 'selenium':
                        from urllib.parse import quote_plus
                        search_url = f"https://duckduckgo.com/?q={quote_plus(search_query)}"
                    elif method == 'api':
                        search_url = f"https://www.google.com/search?q={quote_plus(search_query)}"
                    
                    verification_details = {
                        'search_query': search_query,
                        'search_engine': 'DuckDuckGo' if method == 'selenium' else 'Google',
                        'search_url': search_url,
                        'method': method,
                        'matched_profiles': google_verification.get('linkedin_profiles', []),
                        'search_results_summary': google_verification.get('search_results_summary', [])
                    }
                
                return {
                    'status': 'found_and_verified',
                    'profile': linkedin_found,
                    'alternatives': other_profiles,
                    'google_verification': google_verified_linkedin,
                    'verification_details': verification_details,
                    'recommendation': '✅ LinkedIn profile found in resume AND verified online - Highest authenticity confidence'
                }
            elif linkedin_found and google_verification and google_verification.get('search_attempted') and not cross_verified:
                return {
                    'status': 'found_not_verified',
                    'profile': linkedin_found,
                    'alternatives': other_profiles,
                    'google_verification': google_verified_linkedin,
                    'google_verification': google_verification,
                    'recommendation': '⚠️ WARNING: LinkedIn URL in resume could NOT be verified on Google - Possible fake or deleted profile'
                }
            elif linkedin_found and not google_verification:
                return {
                    'status': 'found_not_checked',
                    'profile': linkedin_found,
                    'alternatives': other_profiles,
                    'google_verification': None,
                    'recommendation': '⚠️ LinkedIn URL in resume but not cross-verified (Google API not configured)'
                }
            elif google_verified_linkedin:
                return {
                    'status': 'verified_online_only',
                    'profile': None,
                    'google_verified_profiles': google_verified_linkedin['profiles'],
                    'alternatives': other_profiles,
                    'google_verification': google_verified_linkedin,
                    'recommendation': '✅ LinkedIn profile verified online (not in resume) - Consider adding to resume for better visibility'
                }
            elif other_profiles:
                return {
                    'status': 'alternative',
                    'profile': None,
                    'alternatives': other_profiles,
                    'google_verification': google_verification,
                    'recommendation': '⚠️ No LinkedIn profile, but found alternative professional profiles. Consider adding LinkedIn URL.'
                }
            else:
                # No profile found anywhere
                google_note = ''
                if google_verification:
                    if google_verification.get('search_attempted'):
                        google_note = ' (Google search performed - no LinkedIn found)'
                    else:
                        google_note = ' (Google search API not configured)'
                
                return {
                    'status': 'missing',
                    'profile': None,
                    'alternatives': [],
                    'google_verification': google_verification,
                    'recommendation': f'❌ No professional profile found{google_note}. Add LinkedIn URL: linkedin.com/in/your-username'
                }
                
        except Exception as e:
            logger.error(f"LinkedIn diagnostics failed: {str(e)}")
            return {
                'status': 'error',
                'profile': None,
                'alternatives': [],
                'recommendation': 'Unable to analyze professional profiles'
            }

    def _get_grammar_diagnostics(self, text_content: str) -> Dict[str, Any]:
        """Get detailed grammar issues"""
        try:
            issues = []
            
            # 1. Excessive capitalization (SCREAMING TEXT)
            words = text_content.split()
            capitalized_words = [w for w in words if w.isupper() and len(w) > 3]
            
            if len(capitalized_words) > len(words) * 0.1:
                issues.append({
                    'type': 'Excessive Capitalization',
                    'severity': 'medium',
                    'examples': capitalized_words[:5],
                    'count': len(capitalized_words),
                    'fix': 'Avoid using all caps. Use normal sentence case.'
                })
            
            # 2. Excessive punctuation
            special_chars = [c for c in text_content if c in '!@#$%^&*()']
            if len(special_chars) > len(text_content) * 0.05:
                issues.append({
                    'type': 'Excessive Special Characters',
                    'severity': 'low',
                    'count': len(special_chars),
                    'fix': 'Reduce use of special characters and punctuation'
                })
            
            # 3. Very short sentences
            sentences = [s.strip() for s in text_content.split('.') if s.strip()]
            short_sentences = [s for s in sentences if len(s.split()) < 3]
            
            if len(short_sentences) > len(sentences) * 0.3:
                issues.append({
                    'type': 'Fragmented Sentences',
                    'severity': 'low',
                    'examples': short_sentences[:3],
                    'count': len(short_sentences),
                    'fix': 'Use complete sentences with proper structure'
                })
            
            return {
                'issues_found': len(issues),
                'details': issues if issues else [{'type': 'No Issues', 'message': '✅ Grammar quality is good'}]
            }
            
        except Exception as e:
            logger.error(f"Grammar diagnostics failed: {str(e)}")
            return {
                'issues_found': 0,
                'details': [{'type': 'Error', 'message': 'Unable to analyze grammar'}]
            }
