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
            r'(?:https?://)?(?:www\.)?linkedin\.com/in/[\w-]+/?',
            r'(?:https?://)?(?:in\.)?linkedin\.com/in/[\w-]+/?',
        ]
        
        # Degree patterns (comprehensive)
        self.degree_patterns = {
            'bachelor': [
                r"B\.?S\.?(?:\s+in\s+)?([\w\s]+)?",
                r"B\.?A\.?(?:\s+in\s+)?([\w\s]+)?",
                r"B\.?Tech\.?(?:\s+in\s+)?([\w\s]+)?",
                r"B\.?E\.?(?:\s+in\s+)?([\w\s]+)?",
                r"Bachelor['']?s?\s+(?:of\s+)?(?:Science|Arts|Engineering|Technology|Computer Science)(?:\s+in\s+)?([\w\s]+)?",
            ],
            'master': [
                r"M\.?S\.?(?:\s+in\s+)?([\w\s]+)?",
                r"M\.?A\.?(?:\s+in\s+)?([\w\s]+)?",
                r"M\.?Tech\.?(?:\s+in\s+)?([\w\s]+)?",
                r"M\.?E\.?(?:\s+in\s+)?([\w\s]+)?",
                r"Master['']?s?\s+(?:of\s+)?(?:Science|Arts|Engineering|Technology|Computer Science)(?:\s+in\s+)?([\w\s]+)?",
                r"MBA",
                r"M\.B\.A\.?",
            ],
            'doctorate': [
                r"Ph\.?D\.?(?:\s+in\s+)?([\w\s]+)?",
                r"Doctorate(?:\s+in\s+)?([\w\s]+)?",
            ],
            'associate': [
                r"A\.?A\.?(?:\s+in\s+)?([\w\s]+)?",
                r"A\.?S\.?(?:\s+in\s+)?([\w\s]+)?",
                r"Associate['']?s?\s+(?:of\s+)?(?:Science|Arts)(?:\s+in\s+)?([\w\s]+)?",
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
                'certifications': self.extract_certifications(text),
                'achievements': self.extract_achievements(lines),
                'summary': self.extract_summary(lines),
            }
        except Exception as e:
            logger.error(f"Error in extract_all: {str(e)}", exc_info=True)
            return self._empty_extraction()
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for better parsing"""
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)
        # Fix common OCR errors
        text = text.replace('Ø', '0')
        return text
    
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
            for line in lines[:10]:  # Check first 10 lines
                line = line.strip()
                
                # Skip lines with emails, phones, or URLs
                if any(char in line for char in ['@', 'http', 'www']):
                    continue
                if re.search(r'\d{3,}', line):
                    continue
                
                # Name is usually 2-4 capitalized words
                words = line.split()
                capitalized = [w for w in words if w and w[0].isupper() and w.isalpha()]
                
                if 2 <= len(capitalized) <= 4 and len(line) < 50:
                    return ' '.join(capitalized)
            
            return None
        except Exception as e:
            logger.error(f"Name extraction error: {e}")
            return None
    
    def extract_location(self, text: str) -> Optional[str]:
        """Extract location/address"""
        try:
            # Look for city, state patterns
            pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?),?\s*([A-Z]{2}|\w+)'
            matches = re.findall(pattern, text)
            
            if matches:
                # Return first match that looks like a city, state
                return f"{matches[0][0]}, {matches[0][1]}"
            
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
                            
                            # Extract field of study from match group
                            if match.groups() and match.group(1):
                                degree_info['field_of_study'] = match.group(1).strip()
                            
                            # Look for institution in next 3 lines
                            for j in range(i, min(i + 4, len(lines))):
                                check_line = lines[j].lower()
                                if any(keyword in check_line for keyword in self.institution_keywords):
                                    degree_info['institution'] = lines[j].strip()
                                    break
                            
                            # Look for years in current and next 2 lines
                            context = ' '.join(lines[i:min(i + 3, len(lines))])
                            years = re.findall(r'\b(19|20)\d{2}\b', context)
                            if years:
                                if len(years) >= 2:
                                    degree_info['start_year'] = years[0]
                                    degree_info['graduation_year'] = years[1]
                                else:
                                    degree_info['graduation_year'] = years[0]
                            
                            # Look for GPA
                            gpa_match = re.search(r'GPA:?\s*([\d.]+)(?:/[\d.]+)?', context, re.IGNORECASE)
                            if gpa_match:
                                degree_info['gpa'] = gpa_match.group(1)
                            
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
                r'(\w+\s+\d{4})\s*[-–to]+\s*(\w+\s+\d{4}|Present)',
                r'(\d{1,2}/\d{4})\s*[-–to]+\s*(\d{1,2}/\d{4}|Present)',
                r'(\d{4})\s*[-–to]+\s*(\d{4}|Present)',
            ]
            
            i = 0
            while i < len(lines):
                line = lines[i]
                
                # Look for date ranges
                for pattern in date_patterns:
                    match = re.search(pattern, line, re.IGNORECASE)
                    if match:
                        exp_info = {
                            'company': None,
                            'title': None,
                            'location': None,
                            'start_date': match.group(1),
                            'end_date': match.group(2),
                            'duration_months': self._calculate_duration(match.group(1), match.group(2)),
                            'responsibilities': [],
                        }
                        
                        # Job title is usually 1-2 lines before date
                        if i > 0:
                            exp_info['title'] = lines[i - 1].strip()
                        
                        # Company is usually on date line or next line
                        # Look for company indicators
                        for j in range(max(0, i - 1), min(i + 3, len(lines))):
                            check_line = lines[j]
                            if any(keyword in check_line.lower() for keyword in ['inc', 'ltd', 'llc', 'corp', 'company', 'technologies']):
                                exp_info['company'] = check_line.strip()
                                break
                        
                        # Extract responsibilities (bullet points after dates)
                        for j in range(i + 1, min(i + 10, len(lines))):
                            resp_line = lines[j].strip()
                            if resp_line.startswith(('•', '-', '*', '○')):
                                exp_info['responsibilities'].append(resp_line.lstrip('•-*○ '))
                            elif not resp_line or any(keyword in resp_line.lower() for keyword in ['education', 'skills', 'certification']):
                                break
                        
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
    
    def extract_certifications(self, text: str) -> List[Dict[str, Any]]:
        """Extract professional certifications"""
        certifications = []
        
        try:
            for pattern in self.certification_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    # Look for year near certification
                    context_start = max(0, text.find(match) - 50)
                    context_end = min(len(text), text.find(match) + len(match) + 50)
                    context = text[context_start:context_end]
                    
                    year_match = re.search(r'\b(19|20)\d{2}\b', context)
                    year = year_match.group(0) if year_match else None
                    
                    certifications.append({
                        'name': match.strip(),
                        'year': year,
                    })
            
            return certifications
        except Exception as e:
            logger.error(f"Certification extraction error: {e}")
            return []
    
    def extract_achievements(self, lines: List[str]) -> List[str]:
        """Extract achievements, awards, and honors"""
        achievements = []
        
        try:
            achievement_keywords = ['award', 'honor', 'achievement', 'recognition', 'published', 'winner']
            
            for i, line in enumerate(lines):
                line_lower = line.lower()
                if any(keyword in line_lower for keyword in achievement_keywords):
                    # Add this line and potential next line
                    achievements.append(line.strip())
                    if i + 1 < len(lines) and lines[i + 1].strip():
                        achievements.append(lines[i + 1].strip())
            
            return achievements[:10]  # Limit to 10 achievements
        except Exception as e:
            logger.error(f"Achievements extraction error: {e}")
            return []
    
    def extract_summary(self, lines: List[str]) -> Optional[str]:
        """Extract professional summary or objective"""
        try:
            summary_keywords = ['summary', 'objective', 'profile', 'about']
            
            for i, line in enumerate(lines):
                line_lower = line.lower()
                if any(keyword in line_lower for keyword in summary_keywords):
                    # Collect next few lines until blank line or next section
                    summary_lines = []
                    for j in range(i + 1, min(i + 10, len(lines))):
                        if not lines[j].strip():
                            break
                        if any(section in lines[j].lower() for section in ['experience', 'education', 'skills']):
                            break
                        summary_lines.append(lines[j].strip())
                    
                    if summary_lines:
                        return ' '.join(summary_lines)
            
            return None
        except Exception as e:
            logger.error(f"Summary extraction error: {e}")
            return None
