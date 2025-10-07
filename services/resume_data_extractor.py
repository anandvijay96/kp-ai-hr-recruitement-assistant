import re
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import phonenumbers
from email_validator import validate_email, EmailNotValidError

logger = logging.getLogger(__name__)

class ResumeDataExtractor:
    """
    Extracts structured data from resume text using regex patterns and NLP.
    Extracts: name, email, phone, LinkedIn, education, work experience, skills
    """

    def __init__(self):
        self.phone_patterns = [
            r'\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}',  # International
            r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # US format
            r'\d{10}',  # 10 digits
        ]
        
        self.email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        
        self.linkedin_patterns = [
            r'(?:https?://)?(?:www\.)?linkedin\.com/in/[\w-]+/?',
            r'(?:https?://)?(?:in\.)?linkedin\.com/in/[\w-]+/?',
        ]
        
        # Common skills to look for
        self.common_skills = [
            'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'ruby', 'php', 'swift', 'kotlin',
            'react', 'angular', 'vue', 'node.js', 'django', 'flask', 'spring', 'express',
            'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch',
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'git',
            'machine learning', 'data science', 'deep learning', 'nlp', 'computer vision',
            'agile', 'scrum', 'devops', 'ci/cd', 'rest api', 'graphql',
            'html', 'css', 'bootstrap', 'tailwind', 'sass', 'webpack',
        ]

    def extract_all(self, text: str) -> Dict[str, Any]:
        """
        Extract all structured data from resume text.
        
        Returns:
            Dict with extracted data: email, phone, linkedin, name, skills, education, experience
        """
        try:
            if not text or len(text.strip()) < 50:
                logger.warning("Text too short for meaningful extraction")
                return self._empty_extraction()
            
            extracted_data = {
                'email': self.extract_email(text),
                'phone': self.extract_phone(text),
                'linkedin_url': self.extract_linkedin(text),
                'name': self.extract_name(text),
                'skills': self.extract_skills(text),
                'education': self.extract_education(text),
                'work_experience': self.extract_work_experience(text),
            }
            
            return extracted_data
        except Exception as e:
            logger.error(f"Unexpected error in extract_all: {str(e)}")
            return self._empty_extraction()

    def _empty_extraction(self) -> Dict[str, Any]:
        """Return empty extraction structure"""
        return {
            'email': None,
            'phone': None,
            'linkedin_url': None,
            'name': None,
            'skills': [],
            'education': [],
            'work_experience': [],
        }

    def extract_email(self, text: str) -> Optional[str]:
        """Extract email address from text"""
        try:
            matches = re.findall(self.email_pattern, text, re.IGNORECASE)
            for email in matches:
                try:
                    # Validate email
                    validated = validate_email(email, check_deliverability=False)
                    return validated.email
                except EmailNotValidError:
                    continue
            return None
        except Exception as e:
            logger.error(f"Error extracting email: {e}")
            return None

    def extract_phone(self, text: str) -> Optional[str]:
        """Extract phone number from text"""
        try:
            for pattern in self.phone_patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    try:
                        # Try to parse and validate phone number
                        phone_obj = phonenumbers.parse(match, None)
                        if phonenumbers.is_valid_number(phone_obj):
                            return phonenumbers.format_number(phone_obj, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
                    except:
                        # If parsing fails, just clean and return the match
                        cleaned = re.sub(r'[^\d+]', '', match)
                        if len(cleaned) >= 10:
                            return match
            return None
        except Exception as e:
            logger.error(f"Error extracting phone: {e}")
            return None

    def extract_linkedin(self, text: str) -> Optional[str]:
        """Extract LinkedIn URL from text"""
        try:
            for pattern in self.linkedin_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    url = match.group(0)
                    # Normalize URL
                    if not url.startswith('http'):
                        url = 'https://' + url
                    return url
            return None
        except Exception as e:
            logger.error(f"Error extracting LinkedIn: {e}")
            return None

    def extract_name(self, text: str) -> Optional[str]:
        """
        Extract candidate name from text.
        Uses heuristics: first 3 lines, capitalized words, common patterns
        """
        try:
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            # Look in first 5 lines for name
            for line in lines[:5]:
                # Skip if line has email or phone (likely contact info, not name)
                if '@' in line or re.search(r'\d{3,}', line):
                    continue
                
                # Name is likely 2-4 capitalized words
                words = line.split()
                capitalized_words = [w for w in words if w and w[0].isupper()]
                
                if 2 <= len(capitalized_words) <= 4 and len(line) < 50:
                    # Likely a name
                    return ' '.join(capitalized_words)
            
            # Fallback: first line that's not too long
            for line in lines[:3]:
                if len(line) < 50 and not '@' in line:
                    return line
            
            return None
        except Exception as e:
            logger.error(f"Error extracting name: {e}")
            return None

    def extract_skills(self, text: str) -> List[str]:
        """Extract technical skills from text"""
        try:
            text_lower = text.lower()
            found_skills = []
            
            for skill in self.common_skills:
                # Use word boundary for better matching
                pattern = r'\b' + re.escape(skill.lower()) + r'\b'
                if re.search(pattern, text_lower):
                    found_skills.append(skill.title())
            
            return list(set(found_skills))  # Remove duplicates
        except Exception as e:
            logger.error(f"Error extracting skills: {e}")
            return []

    def extract_education(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract education information from text.
        Returns list of dicts with: degree, institution, year
        """
        try:
            education_list = []
            
            # Degree patterns
            degree_patterns = [
                r'\b(B\.?S\.?|Bachelor(?:\'?s)?)\s+(?:of\s+)?(?:Science|Arts|Engineering|Technology|Computer Science)?\b',
                r'\b(M\.?S\.?|Master(?:\'?s)?)\s+(?:of\s+)?(?:Science|Arts|Engineering|Technology|Computer Science)?\b',
                r'\b(Ph\.?D\.?|Doctorate)\b',
                r'\b(MBA|M\.B\.A\.)\b',
            ]
            
            lines = text.split('\n')
            
            for i, line in enumerate(lines):
                for pattern in degree_patterns:
                    match = re.search(pattern, line, re.IGNORECASE)
                    if match:
                        degree = match.group(0)
                        
                        # Try to find institution in same or next line
                        institution = None
                        year = None
                        
                        # Look for university/college keywords
                        if i + 1 < len(lines):
                            next_line = lines[i + 1]
                            if any(word in next_line.lower() for word in ['university', 'college', 'institute', 'school']):
                                institution = next_line.strip()
                        
                        # Look for year (4 digits)
                        year_match = re.search(r'\b(19|20)\d{2}\b', line)
                        if year_match:
                            year = year_match.group(0)
                        
                        education_list.append({
                            'degree': degree,
                            'institution': institution,
                            'year': year,
                        })
                        break
            
            return education_list
        except Exception as e:
            logger.error(f"Error extracting education: {e}")
            return []

    def extract_work_experience(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract work experience from text.
        Returns list of dicts with: company, title, start_date, end_date
        """
        try:
            experiences = []
            
            # Date range patterns (e.g., "Jan 2020 - Dec 2022", "2020-2022")
            date_range_patterns = [
                r'(\w+\s+\d{4})\s*[-–to]+\s*(\w+\s+\d{4}|Present)',
                r'(\d{4})\s*[-–to]+\s*(\d{4}|Present)',
            ]
            
            # Company indicators
            company_keywords = ['inc', 'ltd', 'llc', 'corp', 'corporation', 'company', 'technologies', 'systems']
            
            lines = text.split('\n')
            
            for i, line in enumerate(lines):
                # Look for date ranges
                for pattern in date_range_patterns:
                    match = re.search(pattern, line, re.IGNORECASE)
                    if match:
                        start_date = match.group(1)
                        end_date = match.group(2)
                        
                        # Try to find company and title nearby
                        company = None
                        title = None
                        
                        # Check previous line for title
                        if i > 0:
                            prev_line = lines[i - 1].strip()
                            # If previous line is capitalized and not too long, might be title
                            if prev_line and len(prev_line) < 100:
                                title = prev_line
                        
                        # Check current line or next for company
                        for check_line in [line, lines[i + 1] if i + 1 < len(lines) else '']:
                            if any(keyword in check_line.lower() for keyword in company_keywords):
                                company = check_line.strip()
                                break
                        
                        experiences.append({
                            'company': company,
                            'title': title,
                            'start_date': start_date,
                            'end_date': end_date,
                        })
                        break
            
            return experiences
        except Exception as e:
            logger.error(f"Error extracting work experience: {e}")
            return []
