"""
Enhanced Resume Data Extractor
Target: 95%+ accuracy for structured data extraction
Uses advanced regex patterns, context analysis, and heuristics
"""

import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dateutil import parser as date_parser
import phonenumbers
from email_validator import validate_email, EmailNotValidError

logger = logging.getLogger(__name__)


class EnhancedResumeExtractor:
    """Enhanced resume data extraction with 95%+ accuracy target"""
    
    def __init__(self):
        # Contact patterns
        self.email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        self.phone_patterns = [
            r'\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}',
            r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
            r'\d{10}',
        ]
        self.linkedin_patterns = [
            r'(?:https?://)?(?:www\.|in\.)?linkedin\.com/in/[\w-]+/?',
            r'linkedin\.com/in/[\w-]+',
        ]
        
        # Degree patterns (comprehensive) - Order matters! Check PhD before Master's
        self.degree_patterns = {
            'doctorate': [
                r"\bPh\.?D\.?\b(?:\s+in\s+[\w\s]+)?",
                r"\bPhD\b(?:\s+in\s+[\w\s]+)?",
                r"\bDoctorate\b(?:\s+in\s+[\w\s]+)?",
                r"\bDoctor\s+of\s+Philosophy\b(?:\s+in\s+[\w\s]+)?",
            ],
            'master': [
                r"\bMaster['']?s?\s+(?:of\s+)?(?:Science|Arts|Engineering|Technology|Computer Science|Business Administration)\b",
                r"\bM\.S\.(?:\s+in)?(?:\s+[\w\s]+)?",
                r"\bM\.A\.(?:\s+in)?(?:\s+[\w\s]+)?",
                r"\bM\.Tech\.?(?:\s+in)?(?:\s+[\w\s]+)?",
                r"\bM\.E\.(?:\s+in)?(?:\s+[\w\s]+)?",
                r"\bMBA\b",
            ],
            'bachelor': [
                r"\bBachelor['']?s?\s+(?:of\s+)?(?:Science|Arts|Engineering|Technology|Computer Science)\b",
                r"\bB\.S\.(?:\s+in)?(?:\s+[\w\s]+)?",
                r"\bB\.A\.(?:\s+in)?(?:\s+[\w\s]+)?",
                r"\bB\.Tech\.?(?:\s+in)?(?:\s+[\w\s]+)?",
                r"\bB\.E\.(?:\s+in)?(?:\s+[\w\s]+)?",
            ],
            'associate': [
                r"\bAssociate['']?s?\s+(?:of\s+)?(?:Science|Arts)\b",
                r"\bA\.S\.(?:\s+in)?(?:\s+[\w\s]+)?",
                r"\bA\.A\.(?:\s+in)?(?:\s+[\w\s]+)?",
            ]
        }
        
        # Institution indicators
        self.institution_keywords = [
            'university', 'college', 'institute', 'school', 'academy',
            'polytechnic', 'iit', 'mit', 'stanford', 'harvard',
        ]
        
        # Certification patterns
        self.certification_patterns = [
            # Cloud certifications
            r'AWS\s+(?:Certified\s+)?(?:Solutions Architect|Developer|SysOps|DevOps|Security|Data Analytics|Machine Learning)',
            r'Microsoft\s+(?:Certified\s+)?Azure\s+(?:Administrator|Developer|Solutions Architect|DevOps Engineer|Security Engineer|Data Engineer|AI Engineer)',
            r'Google\s+Cloud\s+(?:Certified\s+)?(?:Professional|Associate)?\s*(?:Cloud Architect|Data Engineer|Cloud Developer|Cloud Security Engineer)',
            
            # Project Management
            r'PMP|Project Management Professional',
            r'PRINCE2',
            r'Certified\s+ScrumMaster|CSM',
            r'SAFe|Scaled Agile Framework',
            
            # Programming & Tech
            r'Oracle\s+Certified\s+(?:Associate|Professional|Master)',
            r'Cisco\s+(?:CCNA|CCNP|CCIE)',
            r'CompTIA\s+(?:A\+|Network\+|Security\+|Cloud\+)',
            r'Red\s+Hat\s+Certified',
            r'Kubernetes\s+Certified',
            
            # Data & Analytics
            r'Tableau\s+Certified',
            r'Databricks\s+Certified',
            r'Snowflake\s+(?:SnowPro|Certified)',
        ]
        
        # Month abbreviations for date parsing
        self.months = [
            'january', 'february', 'march', 'april', 'may', 'june',
            'july', 'august', 'september', 'october', 'november', 'december',
            'jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'
        ]
        
        # Comprehensive skills list (200+ skills)
        self.skills_database = self._build_skills_database()
    
    def _build_skills_database(self) -> Dict[str, List[str]]:
        """Build comprehensive skills database categorized by type"""
        return {
            'programming_languages': [
                'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'c', 'ruby',
                'php', 'swift', 'kotlin', 'go', 'rust', 'scala', 'r', 'matlab', 'perl',
                'dart', 'elixir', 'haskell', 'lua', 'groovy', 'objective-c', 'visual basic',
            ],
            'web_frameworks': [
                'react', 'angular', 'vue', 'vue.js', 'svelte', 'next.js', 'nuxt.js',
                'node.js', 'express', 'express.js', 'fastapi', 'django', 'flask',
                'spring', 'spring boot', 'asp.net', 'laravel', 'rails', 'ruby on rails',
                'jquery', 'backbone.js', 'ember.js',
            ],
            'mobile': [
                'react native', 'flutter', 'ionic', 'xamarin', 'android', 'ios',
                'swift ui', 'kotlin multiplatform',
            ],
            'databases': [
                'sql', 'mysql', 'postgresql', 'oracle', 'sql server', 'mongodb',
                'redis', 'cassandra', 'dynamodb', 'elasticsearch', 'neo4j',
                'mariadb', 'sqlite', 'couchdb', 'firebase', 'realm',
            ],
            'cloud_platforms': [
                'aws', 'azure', 'gcp', 'google cloud', 'alibaba cloud', 'ibm cloud',
                'oracle cloud', 'digitalocean', 'heroku', 'netlify', 'vercel',
            ],
            'devops_tools': [
                'docker', 'kubernetes', 'jenkins', 'gitlab ci', 'github actions',
                'travis ci', 'circleci', 'terraform', 'ansible', 'puppet', 'chef',
                'vagrant', 'prometheus', 'grafana', 'elk stack', 'datadog', 'new relic',
            ],
            'data_science_ml': [
                'machine learning', 'deep learning', 'artificial intelligence', 'ai',
                'nlp', 'natural language processing', 'computer vision', 'tensorflow',
                'pytorch', 'keras', 'scikit-learn', 'pandas', 'numpy', 'matplotlib',
                'seaborn', 'jupyter', 'apache spark', 'hadoop', 'airflow',
            ],
            'version_control': [
                'git', 'github', 'gitlab', 'bitbucket', 'svn', 'mercurial',
            ],
            'frontend': [
                'html', 'html5', 'css', 'css3', 'sass', 'scss', 'less',
                'bootstrap', 'tailwind css', 'material ui', 'ant design',
                'webpack', 'vite', 'parcel', 'rollup',
            ],
            'testing': [
                'jest', 'mocha', 'chai', 'jasmine', 'pytest', 'unittest',
                'selenium', 'cypress', 'playwright', 'puppeteer', 'junit',
                'testng', 'cucumber', 'postman',
            ],
            'methodologies': [
                'agile', 'scrum', 'kanban', 'devops', 'ci/cd', 'tdd', 'bdd',
                'test driven development', 'microservices', 'serverless',
                'rest api', 'restful', 'graphql', 'soap', 'grpc',
            ],
            'business_tools': [
                'jira', 'confluence', 'slack', 'trello', 'asana', 'notion',
                'microsoft office', 'excel', 'powerpoint', 'word', 'google workspace',
            ],
        }
    
    def extract_all(self, text: str) -> Dict[str, Any]:
        """Extract all data with enhanced accuracy"""
        try:
            if not text or len(text.strip()) < 50:
                logger.warning("Text too short for extraction")
                return self._empty_extraction()
            
            # Normalize text
            text = self._normalize_text(text)
            lines = text.split('\n')
            
            return {
                'email': self.extract_email(text),
                'phone': self.extract_phone(text),
                'linkedin_url': self.extract_linkedin(text),
                'github_url': self.extract_github(text),
                'portfolio_url': self.extract_portfolio(text),
                'name': self.extract_name(lines),
                'location': self.extract_location(text),
                'skills': self.extract_skills(text),
                'education': self.extract_education_enhanced(lines, text),
                'work_experience': self.extract_work_experience_enhanced(lines, text),
                'certifications': self.extract_certifications_enhanced(lines, text),
                'achievements': self.extract_achievements(lines),
                'summary': self.extract_summary(lines),
                'projects': self.extract_projects(lines, text),
                'languages': self.extract_languages(lines, text),
            }
        except Exception as e:
            logger.error(f"Error in extract_all: {str(e)}", exc_info=True)
            return self._empty_extraction()
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for better parsing"""
        # Fix common OCR errors
        text = text.replace('Ø', '0')
        # Replace multiple spaces on same line with single space, but preserve newlines
        lines = text.split('\n')
        normalized_lines = [re.sub(r'[ \t]+', ' ', line) for line in lines]
        return '\n'.join(normalized_lines)
    
    def _empty_extraction(self) -> Dict[str, Any]:
        """Return empty extraction structure"""
        return {
            'email': None,
            'phone': None,
            'linkedin_url': None,
            'github_url': None,
            'portfolio_url': None,
            'name': None,
            'location': None,
            'skills': [],
            'education': [],
            'work_experience': [],
            'certifications': [],
            'achievements': [],
            'summary': None,
            'projects': [],
            'languages': [],
        }
    
    def extract_email(self, text: str) -> Optional[str]:
        """Extract and validate email"""
        try:
            matches = re.findall(self.email_pattern, text, re.IGNORECASE)
            for email in matches:
                try:
                    validated = validate_email(email, check_deliverability=False)
                    return validated.email
                except EmailNotValidError:
                    continue
            return None
        except Exception as e:
            logger.error(f"Email extraction error: {e}")
            return None
    
    def extract_phone(self, text: str) -> Optional[str]:
        """Extract and format phone number"""
        try:
            for pattern in self.phone_patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    try:
                        phone_obj = phonenumbers.parse(match, None)
                        if phonenumbers.is_valid_number(phone_obj):
                            return phonenumbers.format_number(
                                phone_obj, 
                                phonenumbers.PhoneNumberFormat.INTERNATIONAL
                            )
                    except:
                        cleaned = re.sub(r'[^\d+]', '', match)
                        if len(cleaned) >= 10:
                            return match
            return None
        except Exception as e:
            logger.error(f"Phone extraction error: {e}")
            return None
    
    def extract_linkedin(self, text: str) -> Optional[str]:
        """Extract LinkedIn URL"""
        try:
            for pattern in self.linkedin_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    url = match.group(0)
                    if not url.startswith('http'):
                        url = 'https://' + url
                    return url
            return None
        except Exception as e:
            logger.error(f"LinkedIn extraction error: {e}")
            return None
    
    def extract_github(self, text: str) -> Optional[str]:
        """Extract GitHub URL"""
        try:
            pattern = r'(?:https?://)?(?:www\.)?github\.com/[\w-]+/?'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                url = match.group(0)
                if not url.startswith('http'):
                    url = 'https://' + url
                return url
            return None
        except Exception as e:
            logger.error(f"GitHub extraction error: {e}")
            return None
    
    def extract_portfolio(self, text: str) -> Optional[str]:
        """Extract portfolio/personal website URL"""
        try:
            # Look for common portfolio patterns
            patterns = [
                r'(?:https?://)?(?:www\.)?[\w-]+\.(?:com|io|dev|me|tech|net|org)/?',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    # Exclude known platforms
                    if any(platform in match.lower() for platform in ['linkedin', 'github', 'gmail', 'yahoo', 'outlook']):
                        continue
                    if not match.startswith('http'):
                        match = 'https://' + match
                    return match
            return None
        except Exception as e:
            logger.error(f"Portfolio extraction error: {e}")
            return None
    
    def extract_name(self, lines: List[str]) -> Optional[str]:
        """Enhanced name extraction using multiple heuristics"""
        try:
            # Common section headers to skip
            skip_patterns = [
                r'^(PROFESSIONAL SUMMARY|PROFILE|OBJECTIVE|KEY RESPONSIBILITIES)',
                r'^(CERTIFICATION|CERTIFICATIONS|CONTACT|CONTACT INFORMATION)',
                r'^(SKILLS|TECHNICAL SKILLS|CORE COMPETENCIES)',
                r'^(EDUCATION|ACADEMIC BACKGROUND|QUALIFICATIONS)',
                r'^(EXPERIENCE|WORK EXPERIENCE|EMPLOYMENT HISTORY|PROFESSIONAL EXPERIENCE)',
                r'^(SUMMARY|CAREER SUMMARY|EXECUTIVE SUMMARY)',
                r'^(PROJECTS|KEY PROJECTS|ACHIEVEMENTS|ACCOMPLISHMENTS)',
                r'^(REFERENCES|LANGUAGES|INTERESTS|HOBBIES)',
                r'^(RESUME|CURRICULUM VITAE|CV)',
            ]
            
            for line in lines[:20]:  # Check first 20 lines
                line = line.strip()
                
                # Skip empty lines
                if not line:
                    continue
                
                # Skip section headers
                if any(re.match(pattern, line.upper()) for pattern in skip_patterns):
                    continue
                
                # Skip lines with emails, phones, or URLs
                if any(char in line for char in ['@', 'http', 'www']):
                    continue
                
                # Skip lines with phone numbers (3+ consecutive digits)
                if re.search(r'\d{3,}', line):
                    continue
                
                # Skip lines with special characters commonly in headers (but allow hyphens in names)
                if any(char in line for char in [':', '|', '/', '\\', '•', '●', '○', '.com', '.net']):
                    continue
                
                # Name is usually 2-4 capitalized words
                words = line.split()
                
                # Filter to only capitalized words (allow hyphens)
                capitalized = [w for w in words if w and len(w) > 1 and w[0].isupper() and (w.replace('-', '').isalpha())]
                
                # Check if it looks like a name
                if 2 <= len(capitalized) <= 4 and len(line) < 60:
                    # Additional validation: not all uppercase (likely a header)
                    if not line.isupper():
                        return ' '.join(capitalized)
            
            return None
        except Exception as e:
            logger.error(f"Name extraction error: {e}")
            return None
    
    def extract_location(self, text: str) -> Optional[str]:
        """Extract location/address"""
        try:
            # Look for "Location:" label first - be more specific
            location_match = re.search(r'(?:Location|Address|City|Based in):?\s*([A-Z][a-z]+(?:[\s,]+[A-Z][a-z]+)*)(?:\n|,|\||$)', text, re.IGNORECASE)
            if location_match:
                loc = location_match.group(1).strip()
                # Filter out non-location words
                if len(loc) < 50 and not any(word in loc.lower() for word in ['data', 'implementation', 'manager', 'engineer', 'developer', 'testing', 'product']):
                    return loc
            
            # Look for city, state patterns (City, State format)
            # Common location indicators (near contact info, before professional summary)
            lines = text.split('\n')[:15]  # Check first 15 lines only
            text_top = '\n'.join(lines)
            
            pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?),\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b'
            matches = re.findall(pattern, text_top)
            
            if matches:
                # Filter out common false positives
                forbidden_words = ['data', 'implementation', 'enterprise', 'manager', 'engineer', 'developer', 
                                   'senior', 'junior', 'lead', 'testing', 'product', 'quality', 'assurance',
                                   'email', 'phone', 'linkedin', 'github', 'project', 'program']
                for city, state in matches:
                    # Skip if it looks like a name, email, or job title
                    if '@' in city or '@' in state:
                        continue
                    if any(word in city.lower() for word in forbidden_words):
                        continue
                    if any(word in state.lower() for word in forbidden_words):
                        continue
                    # Skip if state part looks like it's part of a title (e.g., "Implementation")
                    if len(state) > 15:  # States/countries are usually shorter
                        continue
                    return f"{city}, {state}"
            
            return None
        except Exception as e:
            logger.error(f"Location extraction error: {e}")
            return None
    
    def extract_skills(self, text: str) -> List[str]:
        """Enhanced skills extraction with context awareness"""
        try:
            text_lower = text.lower()
            found_skills = set()
            
            # Search all skill categories
            for category, skills_list in self.skills_database.items():
                for skill in skills_list:
                    # Use word boundary for accurate matching
                    pattern = r'\b' + re.escape(skill.lower()) + r'\b'
                    if re.search(pattern, text_lower):
                        # Capitalize skill name properly
                        found_skills.add(self._capitalize_skill(skill))
            
            return sorted(list(found_skills))
        except Exception as e:
            logger.error(f"Skills extraction error: {e}")
            return []
    
    def _capitalize_skill(self, skill: str) -> str:
        """Properly capitalize skill names"""
        # Special cases
        special_cases = {
            'html': 'HTML',
            'css': 'CSS',
            'sql': 'SQL',
            'nosql': 'NoSQL',
            'aws': 'AWS',
            'gcp': 'GCP',
            'api': 'API',
            'ui': 'UI',
            'ux': 'UX',
            'nlp': 'NLP',
            'ai': 'AI',
            'ml': 'ML',
            'ci/cd': 'CI/CD',
            'tdd': 'TDD',
            'bdd': 'BDD',
        }
        
        skill_lower = skill.lower()
        if skill_lower in special_cases:
            return special_cases[skill_lower]
        
        # Default: title case
        return skill.title()
    
    def extract_education_enhanced(self, lines: List[str], full_text: str) -> List[Dict[str, Any]]:
        """Enhanced education extraction with all fields"""
        education_list = []
        
        try:
            i = 0
            while i < len(lines):
                line = lines[i]
                
                # Check for degree patterns
                for degree_level, patterns in self.degree_patterns.items():
                    for pattern in patterns:
                        match = re.search(pattern, line, re.IGNORECASE)
                        if match:
                            degree_info = {
                                'degree_level': degree_level,
                                'degree': match.group(0).strip(),
                                'field_of_study': None,
                                'institution': None,
                                'location': None,
                                'graduation_year': None,
                                'start_year': None,
                                'gpa': None,
                            }
                            
                            # Extract field of study from match group or next line
                            if match.groups() and match.group(1):
                                degree_info['field_of_study'] = match.group(1).strip()
                            
                            # If no field found, check next line (common format: degree on one line, field on next)
                            if not degree_info['field_of_study'] and i + 1 < len(lines):
                                next_line = lines[i + 1].strip()
                                next_line_lower = next_line.lower()
                                # Check if next line looks like a field of study (not institution, not date)
                                if next_line and not any(keyword in next_line_lower for keyword in self.institution_keywords):
                                    if not re.search(r'\d{4}', next_line):  # Not a year
                                        if len(next_line) < 50:  # Reasonable length for field
                                            degree_info['field_of_study'] = next_line
                            
                            # Look for institution in next 3 lines (skip field of study line if used)
                            start_j = i + 2 if degree_info['field_of_study'] and degree_info['field_of_study'] == lines[i + 1].strip() else i + 1
                            for j in range(start_j, min(i + 5, len(lines))):
                                if j >= len(lines):
                                    break
                                check_line = lines[j].strip()
                                check_line_lower = check_line.lower()
                                if any(keyword in check_line_lower for keyword in self.institution_keywords):
                                    degree_info['institution'] = check_line
                                    break
                                # Also check if line looks like an institution (capitalized, reasonable length)
                                elif check_line and len(check_line) < 100 and check_line[0].isupper():
                                    # Not a section header, not the field we already captured
                                    if not any(h in check_line_lower for h in ['education', 'experience', 'skills', 'certification']):
                                        if check_line != degree_info.get('field_of_study'):
                                            degree_info['institution'] = check_line
                                            break
                            
                            # Look for years in current and next 4 lines
                            context = ' '.join(lines[i:min(i + 5, len(lines))])
                            years = re.findall(r'\b((?:19|20)\d{2})\b', context)
                            if years:
                                if len(years) >= 2:
                                    degree_info['start_year'] = years[0]
                                    degree_info['graduation_year'] = years[1]
                                else:
                                    degree_info['graduation_year'] = years[0]
                            
                            # Look for GPA in multiple formats
                            gpa_patterns = [
                                r'GPA:?\s*([\d.]+)(?:/[\d.]+)?',
                                r'Grade:?\s*([\d.]+)(?:/[\d.]+)?',
                                r'CGPA:?\s*([\d.]+)(?:/[\d.]+)?',
                            ]
                            for gpa_pattern in gpa_patterns:
                                gpa_match = re.search(gpa_pattern, context, re.IGNORECASE)
                                if gpa_match:
                                    degree_info['gpa'] = gpa_match.group(1)
                                    break
                            
                            education_list.append(degree_info)
                            break
                
                i += 1
            
            return education_list
        except Exception as e:
            logger.error(f"Education extraction error: {e}")
            return []
    
    def extract_work_experience_enhanced(self, lines: List[str], full_text: str) -> List[Dict[str, Any]]:
        """Enhanced work experience extraction"""
        experiences = []
        
        try:
            date_patterns = [
                r'(\w+\s+\d{4})\s*[-–to]+\s*(\w+\s+\d{4}|Present|Current)',
                r'(\d{1,2}/\d{4})\s*[-–to]+\s*(\d{1,2}/\d{4}|Present|Current)',
                r'(\d{4})\s*[-–to]+\s*(\d{4}|Present|Current)',
            ]
            
            # Skip section headers
            skip_headers = ['experience', 'work experience', 'professional experience', 'employment history']
            
            # Education section indicators - don't extract work experience from education section
            education_indicators = ['education', 'academic', 'qualifications', 'degree', 'university', 'college', 'school']
            
            i = 0
            in_education_section = False
            
            while i < len(lines):
                line = lines[i]
                line_lower = line.lower().strip()
                
                # Check if we're in education section
                if any(edu_keyword in line_lower for edu_keyword in education_indicators):
                    if len(line_lower) < 50:  # Likely a section header
                        in_education_section = True
                        i += 1
                        continue
                
                # Skip if in education section
                if in_education_section:
                    # Check if we've left education section (new section header)
                    if any(header in line_lower for header in skip_headers):
                        in_education_section = False
                    else:
                        i += 1
                        continue
                
                # Skip section headers
                if any(header == line_lower for header in skip_headers):
                    i += 1
                    continue
                
                # Look for date ranges
                for pattern in date_patterns:
                    match = re.search(pattern, line, re.IGNORECASE)
                    if match:
                        end_date_str = match.group(2)
                        is_current = 'present' in end_date_str.lower() or 'current' in end_date_str.lower()
                        
                        exp_info = {
                            'company': None,
                            'title': None,
                            'location': None,
                            'start_date': match.group(1),
                            'end_date': end_date_str,
                            'is_current': is_current,
                            'duration_months': self._calculate_duration(match.group(1), end_date_str),
                            'responsibilities': [],
                            'description': None,
                        }
                        
                        # Extract title and company from surrounding lines
                        # Typical structure:
                        # Line i-2: Job Title
                        # Line i-1: Company Name, Location
                        # Line i: Date Range
                        
                        # First, find company (has keywords, location, or is line before title)
                        for j in range(max(0, i - 2), min(i + 1, len(lines))):
                            check_line = lines[j].strip()
                            if check_line and j != i:  # Don't check the date line itself
                                # Check for company keywords or location patterns
                                has_company_keyword = any(keyword in check_line.lower() for keyword in ['inc', 'ltd', 'llc', 'corp', 'company', 'technologies', 'corporation', 'services', 'systems', 'solutions', 'group', 'consulting'])
                                has_location = re.search(r',\s*[A-Z]{2}(?:\s|$)', check_line) or re.search(r',\s*[A-Z][a-z]+', check_line)
                                
                                if has_company_keyword or has_location:
                                    exp_info['company'] = check_line
                                    break
                        
                        # If still no company, use line before title (i-2) or after title (i-1)
                        if not exp_info['company']:
                            if i > 1:
                                potential_company = lines[i - 1].strip()
                                # Make sure it's not the title and not a section header
                                if potential_company and potential_company != exp_info.get('title'):
                                    if not any(h in potential_company.lower() for h in skip_headers):
                                        # Check it's not too long (likely not a company name)
                                        if len(potential_company) < 100 and not potential_company.startswith(('•', '-', '*')):
                                            exp_info['company'] = potential_company
                        
                        # Then extract title (line before company or 2 lines before date)
                        if i >= 2:
                            potential_title = lines[i - 2].strip()
                            # Validate it's not a section header
                            if potential_title and not any(h in potential_title.lower() for h in skip_headers):
                                # Check if it's not the company line
                                if potential_title != exp_info.get('company'):
                                    exp_info['title'] = potential_title
                        
                        # If no title found, try line before date
                        if not exp_info['title'] and i > 0:
                            potential_title = lines[i - 1].strip()
                            if potential_title and potential_title != exp_info.get('company'):
                                if not any(h in potential_title.lower() for h in skip_headers):
                                    exp_info['title'] = potential_title
                        
                        # Extract responsibilities (bullet points after dates)
                        responsibilities = []
                        for j in range(i + 1, min(i + 15, len(lines))):
                            resp_line = lines[j].strip()
                            if resp_line.startswith(('•', '-', '*', '○', '●')):
                                clean_resp = resp_line.lstrip('•-*○● ').strip()
                                if clean_resp:
                                    responsibilities.append(clean_resp)
                            elif not resp_line:
                                # Empty line might indicate end of section
                                if responsibilities:
                                    break
                            elif any(keyword in resp_line.lower() for keyword in ['education', 'skills', 'certification', 'project']):
                                break
                            elif re.search(r'\d{4}\s*[-–]\s*\d{4}', resp_line):
                                # Another date range found, stop
                                break
                        
                        exp_info['responsibilities'] = responsibilities
                        
                        # Create description from responsibilities
                        if responsibilities:
                            exp_info['description'] = ' '.join(responsibilities[:3])  # First 3 responsibilities
                        
                        experiences.append(exp_info)
                        break
                
                i += 1
            
            return experiences
        except Exception as e:
            logger.error(f"Work experience extraction error: {e}")
            return []
    
    def _calculate_duration(self, start: str, end: str) -> Optional[int]:
        """Calculate duration in months between two dates"""
        try:
            if 'present' in end.lower():
                end = datetime.now().strftime('%b %Y')
            
            start_date = date_parser.parse(start, fuzzy=True)
            end_date = date_parser.parse(end, fuzzy=True)
            
            months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
            return max(0, months)
        except:
            return None
    
    def extract_certifications_enhanced(self, lines: List[str], text: str) -> List[Dict[str, Any]]:
        """Extract professional certifications with enhanced details"""
        certifications = []
        seen_certs = set()
        
        try:
            # First, try pattern-based extraction
            for pattern in self.certification_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    if match.lower() in seen_certs:
                        continue
                    seen_certs.add(match.lower())
                    
                    # Look for year and issuer near certification
                    context_start = max(0, text.find(match) - 100)
                    context_end = min(len(text), text.find(match) + len(match) + 100)
                    context = text[context_start:context_end]
                    
                    # Extract year
                    year_match = re.search(r'\b(19|20)\d{2}\b', context)
                    issue_date = year_match.group(0) if year_match else None
                    
                    # Extract issuer
                    issuer = None
                    if 'aws' in match.lower():
                        issuer = 'Amazon Web Services'
                    elif 'azure' in match.lower() or 'microsoft' in match.lower():
                        issuer = 'Microsoft'
                    elif 'google' in match.lower():
                        issuer = 'Google Cloud'
                    elif 'cisco' in match.lower():
                        issuer = 'Cisco'
                    elif 'pmp' in match.lower():
                        issuer = 'Project Management Institute'
                    
                    # Extract credential ID
                    credential_match = re.search(r'(?:credential|certificate)\s*(?:id|#)?:?\s*([A-Z0-9-]+)', context, re.IGNORECASE)
                    credential_id = credential_match.group(1) if credential_match else None
                    
                    # Extract expiry date
                    expiry_match = re.search(r'expir(?:es|y|ed)?:?\s*(\w+\s+\d{4}|\d{4})', context, re.IGNORECASE)
                    expiry_date = expiry_match.group(1) if expiry_match else None
                    
                    certifications.append({
                        'name': match.strip(),
                        'issuer': issuer,
                        'issue_date': issue_date,
                        'expiry_date': expiry_date,
                        'credential_id': credential_id,
                    })
            
            # Also look for certification section
            cert_section_keywords = ['certification', 'certifications', 'professional certifications', 'licenses']
            in_cert_section = False
            
            for i, line in enumerate(lines):
                line_lower = line.lower().strip()
                
                # Check if entering certification section
                if any(keyword == line_lower for keyword in cert_section_keywords):
                    in_cert_section = True
                    continue
                
                # Check if leaving certification section
                if in_cert_section and line_lower in ['education', 'experience', 'skills', 'projects']:
                    in_cert_section = False
                
                # Extract certifications from section
                if in_cert_section and line.strip():
                    # Skip lines that look like section headers or work experience
                    if line.strip().isupper() or len(line.strip()) < 5:
                        continue
                    
                    # Skip lines with file paths or URLs
                    if 'file:///' in line.lower() or 'http' in line.lower():
                        continue
                    
                    # Skip lines that look like work experience (company names, job titles)
                    work_indicators = ['lead', 'engineer', 'specialist', 'manager', 'developer', 'analyst', 'consultant']
                    if any(indicator in line.lower() for indicator in work_indicators):
                        # Check if it's followed by a date range (work experience pattern)
                        if re.search(r'\d{4}\s*-\s*\d{4}|\d{4}\s*-\s*present', line.lower()):
                            continue
                    
                    # Look for bullet points or numbered items
                    cert_match = re.match(r'^[•\-*●○]?\s*(.+?)(?:\s*\((\d{4})\))?$', line.strip())
                    if cert_match:
                        cert_name = cert_match.group(1).strip()
                        year = cert_match.group(2) if cert_match.group(2) else None
                        
                        # Additional validation: certification names usually contain certain keywords
                        cert_keywords = ['certified', 'certification', 'certificate', 'professional', 'associate', 'expert', 'specialist']
                        has_cert_keyword = any(keyword in cert_name.lower() for keyword in cert_keywords)
                        
                        # Avoid duplicates and validate
                        if cert_name.lower() not in seen_certs and len(cert_name) > 5 and (has_cert_keyword or len(certifications) == 0):
                            seen_certs.add(cert_name.lower())
                            certifications.append({
                                'name': cert_name,
                                'issuer': None,
                                'issue_date': year,
                                'expiry_date': None,
                                'credential_id': None,
                            })
            
            return certifications
        except Exception as e:
            logger.error(f"Certification extraction error: {e}")
            return []
    
    def extract_achievements(self, lines: List[str]) -> List[str]:
        """Extract achievements, awards, and honors"""
        achievements = []
        
        try:
            achievement_keywords = ['award', 'honor', 'achievement', 'recognition', 'published', 'winner', 'recipient']
            section_keywords = ['awards', 'achievements', 'honors', 'accomplishments', 'publications']
            
            in_achievement_section = False
            
            for i, line in enumerate(lines):
                line_lower = line.lower().strip()
                
                # Check if entering achievement section
                if any(keyword == line_lower for keyword in section_keywords):
                    in_achievement_section = True
                    continue
                
                # Check if leaving achievement section
                if in_achievement_section and line_lower in ['education', 'experience', 'skills', 'certifications']:
                    in_achievement_section = False
                
                # Extract from section
                if in_achievement_section and line.strip():
                    # Extract bullet points
                    if line.strip().startswith(('•', '-', '*', '○', '●')):
                        clean_line = line.strip().lstrip('•-*○● ').strip()
                        if clean_line:
                            achievements.append(clean_line)
                    elif line.strip() and not line.strip().isupper():
                        achievements.append(line.strip())
                
                # Also check for achievement keywords anywhere
                elif any(keyword in line_lower for keyword in achievement_keywords):
                    if line.strip() and not line.strip().isupper():
                        achievements.append(line.strip())
            
            # Remove duplicates while preserving order
            seen = set()
            unique_achievements = []
            for ach in achievements:
                if ach.lower() not in seen:
                    seen.add(ach.lower())
                    unique_achievements.append(ach)
            
            return unique_achievements[:10]  # Limit to 10 achievements
        except Exception as e:
            logger.error(f"Achievements extraction error: {e}")
            return []
    
    def extract_summary(self, lines: List[str]) -> Optional[str]:
        """Extract professional summary or objective"""
        try:
            summary_keywords = [
                'professional summary', 'summary', 'profile', 'objective',
                'career objective', 'about me', 'introduction', 'overview',
                'career summary', 'executive summary', 'professional profile'
            ]
            
            # Section headers that indicate end of summary
            end_sections = [
                'experience', 'work experience', 'employment', 'professional experience',
                'education', 'academic', 'skills', 'technical skills', 'core competencies',
                'projects', 'certifications', 'achievements'
            ]
            
            for i, line in enumerate(lines):
                line_lower = line.lower().strip()
                
                # Check if this line is a summary header
                if any(keyword in line_lower for keyword in summary_keywords):
                    # Collect next few lines until blank line or next section
                    summary_lines = []
                    for j in range(i + 1, min(i + 20, len(lines))):
                        next_line = lines[j].strip()
                        
                        # Stop at blank line
                        if not next_line:
                            break
                        
                        # Stop at next section header
                        if any(section in next_line.lower() for section in end_sections):
                            break
                        
                        # Skip lines that look like headers (all caps, short)
                        if next_line.isupper() and len(next_line) < 30:
                            break
                        
                        summary_lines.append(next_line)
                    
                    if summary_lines:
                        summary_text = ' '.join(summary_lines)
                        # Validate length (reasonable summary is 30-1000 chars)
                        if 30 <= len(summary_text) <= 1000:
                            return summary_text
            
            return None
        except Exception as e:
            logger.error(f"Summary extraction error: {e}")
            return None
    
    def extract_projects(self, lines: List[str], text: str) -> List[Dict[str, Any]]:
        """Extract projects with name, description, and technologies"""
        projects = []
        
        try:
            project_keywords = ['projects', 'key projects', 'major projects', 'project experience']
            in_project_section = False
            current_project = None
            
            for i, line in enumerate(lines):
                line_lower = line.lower().strip()
                
                # Check if entering project section
                if any(keyword == line_lower for keyword in project_keywords):
                    in_project_section = True
                    continue
                
                # Check if leaving project section
                if in_project_section and line_lower in ['education', 'experience', 'skills', 'certifications']:
                    if current_project:
                        projects.append(current_project)
                    in_project_section = False
                    break
                
                if in_project_section and line.strip():
                    # Check if line starts with bullet - it's a description
                    if line.strip().startswith(('•', '-', '*', '○', '●')):
                        if current_project:
                            desc_line = line.strip().lstrip('•-*○● ').strip()
                            if desc_line:
                                current_project['description'].append(desc_line)
                                
                                # Extract technologies from description
                                tech_match = re.search(r'technolog(?:ies|y):?\s*(.+)', desc_line, re.IGNORECASE)
                                if tech_match:
                                    tech_str = tech_match.group(1)
                                    # Split by common delimiters
                                    techs = re.split(r'[,;|]', tech_str)
                                    current_project['technologies'].extend([t.strip() for t in techs if t.strip()])
                    else:
                        # This is likely a project name
                        # Save previous project
                        if current_project:
                            projects.append(current_project)
                        
                        # Start new project - remove leading numbers/bullets
                        project_name = re.sub(r'^[\d\.\)]+\s*', '', line.strip())
                        current_project = {
                            'name': project_name,
                            'description': [],
                            'technologies': [],
                        }
            
            # Add last project
            if current_project:
                projects.append(current_project)
            
            # Clean up projects
            for project in projects:
                project['description'] = ' '.join(project['description'])
                # Remove duplicates from technologies
                project['technologies'] = list(set(project['technologies']))
            
            return projects
        except Exception as e:
            logger.error(f"Projects extraction error: {e}")
            return []
    
    def extract_languages(self, lines: List[str], text: str) -> List[Dict[str, str]]:
        """Extract languages with proficiency levels"""
        languages = []
        seen = set()  # Track seen languages to avoid duplicates
        
        try:
            language_keywords = ['languages', 'language skills', 'language proficiency']
            proficiency_levels = {
                'native': 'native',
                'fluent': 'fluent',
                'professional': 'professional',
                'working': 'working',
                'intermediate': 'intermediate',
                'basic': 'basic',
                'elementary': 'elementary',
                'beginner': 'beginner',
            }
            
            # Common languages
            common_languages = [
                'english', 'spanish', 'french', 'german', 'italian', 'portuguese',
                'chinese', 'mandarin', 'japanese', 'korean', 'arabic', 'russian',
                'hindi', 'bengali', 'punjabi', 'tamil', 'telugu', 'marathi',
                'dutch', 'swedish', 'norwegian', 'danish', 'finnish', 'polish',
                'turkish', 'vietnamese', 'thai', 'indonesian', 'malay',
            ]
            
            in_language_section = False
            
            for i, line in enumerate(lines):
                line_lower = line.lower().strip()
                
                # Check if entering language section
                if any(keyword == line_lower for keyword in language_keywords):
                    in_language_section = True
                    continue
                
                # Check if leaving language section
                if in_language_section and line_lower in ['education', 'experience', 'skills', 'certifications', 'projects']:
                    in_language_section = False
                    break
                
                # Extract from section
                if in_language_section and line.strip():
                    # Pattern: Language: Proficiency or Language (Proficiency)
                    lang_match = re.findall(r'([A-Za-z]+)\s*[:\(]?\s*([A-Za-z\s/]+)?[\)]?', line)
                    
                    for match in lang_match:
                        lang_name = match[0].strip()
                        proficiency = match[1].strip() if match[1] else None
                        
                        # Validate it's a real language
                        if lang_name.lower() in common_languages:
                            # Normalize proficiency
                            normalized_prof = None
                            if proficiency:
                                for key, value in proficiency_levels.items():
                                    if key in proficiency.lower():
                                        normalized_prof = value
                                        break
                            
                            languages.append({
                                'language': lang_name.capitalize(),
                                'proficiency': normalized_prof,
                            })
                
            # Also check for simple format: "Languages: English, Spanish, French" anywhere in text
            for line in lines:
                line_lower = line.lower().strip()
                if 'language' in line_lower and ':' in line:
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        lang_list = parts[1].strip()
                        # Split by commas or spaces
                        potential_langs = re.split(r'[,;]|\s+', lang_list)
                        for lang in potential_langs:
                            lang = lang.strip()
                            if lang and len(lang) > 2:  # At least 3 characters
                                lang_lower = lang.lower()
                                if lang_lower in common_languages:
                                    if lang_lower not in seen:
                                        seen.add(lang_lower)
                                        languages.append({
                                            'language': lang.capitalize(),
                                            'proficiency': None,
                                        })
            
            return languages
        except Exception as e:
            logger.error(f"Languages extraction error: {e}")
            return []
