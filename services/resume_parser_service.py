"""Resume parser service to extract structured data from resumes"""
import re
import logging
from typing import Dict, List, Optional
from datetime import datetime
import docx
import PyPDF2
from io import BytesIO

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

logger = logging.getLogger(__name__)


class ResumeParserService:
    """Service for parsing resume content and extracting structured data"""
    
    def __init__(self):
        # Common patterns for extraction
        # More flexible email pattern that handles edge cases
        self.email_pattern = r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}'
        self.phone_pattern = r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        self.linkedin_pattern = r'(?:https?://)?(?:www\.)?linkedin\.com/in/[\w-]+'
        self.github_pattern = r'(?:https?://)?(?:www\.)?github\.com/[\w-]+'
        
        # Education keywords
        self.education_keywords = [
            'education', 'academic', 'qualification', 'degree', 'university', 
            'college', 'school', 'bachelor', 'master', 'phd', 'diploma'
        ]
        
        # Experience keywords
        self.experience_keywords = [
            'experience', 'employment', 'work history', 'professional experience',
            'career', 'positions held', 'work experience'
        ]
        
        # Skills keywords
        self.skills_keywords = [
            'skills', 'technical skills', 'core competencies', 'expertise',
            'technologies', 'tools', 'proficiencies'
        ]
        
        # Certification keywords
        self.certification_keywords = [
            'certification', 'certificate', 'certified', 'license', 'accreditation'
        ]
    
    async def parse_resume(self, file_content: bytes, file_type: str, file_path: str = None) -> Dict:
        """
        Parse resume and extract structured data
        
        Args:
            file_content: Resume file content as bytes
            file_type: File type (pdf, docx, txt)
            file_path: Optional file path for reading
            
        Returns:
            Dictionary with parsed data
        """
        try:
            # Extract text based on file type
            text = await self._extract_text(file_content, file_type)
            
            if not text:
                logger.warning("No text extracted from resume")
                return self._empty_parsed_data()
            
            # Parse different sections
            parsed_data = {
                "name": self._extract_name(text),
                "email": self._extract_email(text),
                "phone": self._extract_phone(text),
                "linkedin": self._extract_linkedin(text),
                "github": self._extract_github(text),
                "education": self._extract_education(text),
                "experience": self._extract_experience(text),
                "skills": self._extract_skills(text),
                "certifications": self._extract_certifications(text),
                "summary": self._extract_summary(text),
                "total_experience_years": self._calculate_experience_years(text),
                "extracted_text": text[:5000],  # Store first 5000 chars
                "parsed_at": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Successfully parsed resume. Found name: {parsed_data.get('name')}")
            return parsed_data
            
        except Exception as e:
            logger.error(f"Error parsing resume: {str(e)}")
            return self._empty_parsed_data()
    
    async def parse_resume_structured(self, file_content: bytes, file_type: str) -> Dict:
        """
        Parse resume and return structured data compatible with ParsedResumeData schema
        
        Args:
            file_content: Resume file content as bytes
            file_type: File type (pdf, docx, txt)
            
        Returns:
            Dictionary compatible with ParsedResumeData schema
        """
        try:
            # Get basic parsed data
            basic_data = await self.parse_resume(file_content, file_type)
            
            # Transform to structured format
            structured_data = {
                "personal_info": {
                    "name": basic_data.get("name") or "Unknown",
                    "email": basic_data.get("email"),
                    "phone": basic_data.get("phone"),
                    "linkedin_url": basic_data.get("linkedin"),
                    "location": None,  # TODO: Extract location
                    "confidence": {
                        "name": 0.9 if basic_data.get("name") else 0.0,
                        "email": 1.0 if basic_data.get("email") else 0.0,
                        "phone": 0.95 if basic_data.get("phone") else 0.0
                    }
                },
                "education": self._transform_education(basic_data.get("education", [])),
                "experience": self._transform_experience(basic_data.get("experience", [])),
                "skills": self._transform_skills(basic_data.get("skills", [])),
                "certifications": self._transform_certifications(basic_data.get("certifications", [])),
                "total_experience_months": (basic_data.get("total_experience_years") or 0) * 12,
                "summary": basic_data.get("summary")
            }
            
            return structured_data
            
        except Exception as e:
            logger.error(f"Error parsing resume to structured format: {str(e)}")
            return self._empty_structured_data()
    
    def _transform_education(self, education_list: List[Dict]) -> List[Dict]:
        """Transform education data to structured format"""
        transformed = []
        for edu in education_list:
            transformed.append({
                "degree": edu.get("degree", ""),
                "field": None,  # Extract from degree if possible
                "institution": edu.get("college", ""),
                "location": None,
                "start_date": None,
                "end_date": edu.get("year"),
                "gpa": edu.get("gpa"),
                "confidence": 0.85
            })
        return transformed
    
    def _transform_experience(self, experience_list: List[Dict]) -> List[Dict]:
        """Transform experience data to structured format"""
        transformed = []
        for exp in experience_list:
            transformed.append({
                "company": exp.get("company", ""),
                "title": exp.get("title", ""),
                "location": None,
                "start_date": None,
                "end_date": None,
                "duration_months": None,
                "description": None,
                "achievements": [],
                "confidence": 0.80
            })
        return transformed
    
    def _transform_skills(self, skills_list: List[str]) -> List[Dict]:
        """Transform skills data to structured format"""
        transformed = []
        for skill in skills_list:
            transformed.append({
                "name": skill,
                "category": "technical",
                "proficiency": None,
                "confidence": 0.90
            })
        return transformed
    
    def _transform_certifications(self, certifications_list: List[str]) -> List[Dict]:
        """Transform certifications data to structured format"""
        transformed = []
        for cert in certifications_list:
            transformed.append({
                "name": cert,
                "issuer": None,
                "date": None,
                "expiry_date": None,
                "credential_id": None,
                "confidence": 0.85
            })
        return transformed
    
    def _empty_structured_data(self) -> Dict:
        """Return empty structured data"""
        return {
            "personal_info": {
                "name": "Unknown",
                "email": None,
                "phone": None,
                "linkedin_url": None,
                "location": None,
                "confidence": {}
            },
            "education": [],
            "experience": [],
            "skills": [],
            "certifications": [],
            "total_experience_months": None,
            "summary": None
        }
    
    async def _extract_text(self, file_content: bytes, file_type: str) -> str:
        """Extract text from different file formats"""
        try:
            if file_type == 'pdf':
                return self._extract_text_from_pdf(file_content)
            elif file_type == 'docx':
                return self._extract_text_from_docx(file_content)
            elif file_type == 'txt':
                return file_content.decode('utf-8', errors='ignore')
            else:
                logger.warning(f"Unsupported file type: {file_type}")
                return ""
        except Exception as e:
            logger.error(f"Error extracting text: {str(e)}")
            return ""
    
    def _extract_text_from_pdf(self, file_content: bytes) -> str:
        """Extract text from PDF with improved handling using multiple methods"""
        text = ""
        
        # Method 1: Try pdfplumber first (more reliable for text extraction)
        if PDFPLUMBER_AVAILABLE:
            try:
                pdf_file = BytesIO(file_content)
                with pdfplumber.open(pdf_file) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                
                if text.strip():
                    logger.info("Successfully extracted text using pdfplumber")
                    return self._clean_extracted_text(text)
            except Exception as e:
                logger.warning(f"pdfplumber extraction failed: {str(e)}, trying PyPDF2")
        
        # Method 2: Fallback to PyPDF2
        try:
            pdf_file = BytesIO(file_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text = ""
            for page in pdf_reader.pages:
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                except Exception as e:
                    logger.warning(f"Error extracting page: {str(e)}")
                    continue
            
            if text.strip():
                logger.info("Successfully extracted text using PyPDF2")
                return self._clean_extracted_text(text)
            else:
                logger.warning("PDF text extraction yielded very little text")
                return ""
                
        except Exception as e:
            logger.error(f"Error extracting PDF text: {str(e)}")
            return ""
    
    def _clean_extracted_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        # Don't over-normalize - preserve line breaks for better section detection
        # Just clean up excessive whitespace
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            line = ' '.join(line.split())  # Remove extra spaces
            if line:
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines).strip()
    
    def _extract_text_from_docx(self, file_content: bytes) -> str:
        """Extract text from DOCX"""
        try:
            doc = docx.Document(BytesIO(file_content))
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text.strip()
        except Exception as e:
            logger.error(f"Error extracting DOCX text: {str(e)}")
            return ""
    
    def _extract_name(self, text: str) -> Optional[str]:
        """Extract candidate name (usually first line or after 'Name:')"""
        try:
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            # Look for "Name:" pattern
            for line in lines[:10]:  # Check first 10 lines
                if re.search(r'name\s*:', line, re.IGNORECASE):
                    name = re.sub(r'name\s*:\s*', '', line, flags=re.IGNORECASE).strip()
                    if name and len(name.split()) <= 5:  # Reasonable name length
                        return name
            
            # If not found, assume first non-empty line is the name
            for line in lines[:5]:
                # Skip lines that look like headers or contact info
                if not any(keyword in line.lower() for keyword in ['resume', 'cv', 'curriculum', '@', 'phone', 'email']):
                    if 2 <= len(line.split()) <= 5:  # Reasonable name length
                        return line
            
            return None
        except Exception as e:
            logger.error(f"Error extracting name: {str(e)}")
            return None
    
    def _extract_email(self, text: str) -> Optional[str]:
        """Extract email address with improved accuracy"""
        try:
            # Find all potential email addresses
            emails = re.findall(self.email_pattern, text, re.IGNORECASE)
            
            if not emails:
                return None
            
            # Filter out invalid emails and prioritize valid ones
            valid_emails = []
            for email in emails:
                email = email.strip()
                # Skip if email is too short or doesn't have proper format
                if len(email) < 5 or email.count('@') != 1:
                    continue
                # Skip common false positives
                if any(skip in email.lower() for skip in ['example.com', 'test.com', 'domain.com']):
                    continue
                valid_emails.append(email)
            
            # Return the first valid email found
            return valid_emails[0] if valid_emails else None
            
        except Exception as e:
            logger.error(f"Error extracting email: {str(e)}")
            return None
    
    def _extract_phone(self, text: str) -> Optional[str]:
        """Extract phone number"""
        try:
            phones = re.findall(self.phone_pattern, text)
            return phones[0] if phones else None
        except Exception as e:
            logger.error(f"Error extracting phone: {str(e)}")
            return None
    
    def _extract_linkedin(self, text: str) -> Optional[str]:
        """Extract LinkedIn URL"""
        try:
            linkedin = re.findall(self.linkedin_pattern, text, re.IGNORECASE)
            return linkedin[0] if linkedin else None
        except Exception as e:
            logger.error(f"Error extracting LinkedIn: {str(e)}")
            return None
    
    def _extract_github(self, text: str) -> Optional[str]:
        """Extract GitHub URL"""
        try:
            github = re.findall(self.github_pattern, text, re.IGNORECASE)
            return github[0] if github else None
        except Exception as e:
            logger.error(f"Error extracting GitHub: {str(e)}")
            return None
    
    def _extract_education(self, text: str) -> List[Dict]:
        """Extract comprehensive education information"""
        try:
            education = []
            lines = text.split('\n')
            
            # Find education section
            education_start = -1
            for i, line in enumerate(lines):
                if any(keyword in line.lower() for keyword in self.education_keywords):
                    education_start = i
                    logger.info(f"Found education section at line {i}: {line[:50]}")
                    break
            
            if education_start == -1:
                logger.warning("No education section header found in resume")
                # Try to find degrees anywhere in the document as fallback
                return self._extract_education_fallback(text)
            
            # Extract education entries (next 20 lines after education header)
            education_lines = lines[education_start:education_start + 20]
            education_text = '\n'.join(education_lines)
            
            # Pattern to match degree with various formats - more comprehensive
            degree_patterns = [
                # Standard abbreviations
                r'\b(B\.?\s?E\.?|B\.?\s?Tech|M\.?\s?E\.?|M\.?\s?Tech|B\.?\s?S\.?c?|M\.?\s?S\.?c?|MBA|BBA|MCA|BCA)\b',
                # Full names
                r'\b(Bachelor(?:\s+of)?|Master(?:\s+of)?|PhD|Doctorate)\b',
                # With "in" or "of"
                r'\b(Bachelor\s+(?:of|in)\s+\w+|Master\s+(?:of|in)\s+\w+)\b',
                # Professional degrees
                r'\b(Diploma|Post\s+Graduate)\b'
            ]
            
            # Extract structured education data
            for i, line in enumerate(education_lines):
                edu_entry = {}
                
                # Check if line contains a degree
                for pattern in degree_patterns:
                    match = re.search(pattern, line, re.IGNORECASE)
                    if match:
                        # Extract the full line for processing
                        full_line = line.strip()
                        
                        # Try to extract degree with field of study
                        degree_with_field = re.search(
                            r'(B\.?\s?E\.?|B\.?\s?Tech|M\.?\s?E\.?|M\.?\s?Tech|B\.?\s?S\.?c?|M\.?\s?S\.?c?|MBA|BBA|MCA|BCA|Bachelor|Master|PhD)[\s,]*(?:in\s+|of\s+)?([A-Za-z\s&\(\)]+?)(?:\s+\d{4}|\s+at|\s+from|\s+-|$)',
                            full_line,
                            re.IGNORECASE
                        )
                        
                        if degree_with_field:
                            degree_type = degree_with_field.group(1).strip()
                            field = degree_with_field.group(2).strip() if len(degree_with_field.groups()) > 1 else ""
                            
                            # Clean up field name
                            field = re.sub(r'\s+and\s+', ' & ', field)
                            field = re.sub(r'\s+\(.*?\)', '', field)  # Remove parentheses content
                            field = field.strip()
                            
                            # Remove common non-field words
                            field = re.sub(r'\b(from|at|college|university|institute)\b', '', field, flags=re.IGNORECASE)
                            field = field.strip()
                            
                            # Construct clean degree name
                            if field and len(field) > 2 and len(field) < 50:
                                edu_entry['degree'] = f"{degree_type} {field}"
                            else:
                                edu_entry['degree'] = degree_type
                        else:
                            # Fallback: just use the matched text
                            edu_entry['degree'] = match.group(1).strip()
                        
                        # Look for college/university in the same line or next few lines
                        college_keywords = ['university', 'college', 'institute', 'school']
                        for j in range(i, min(i + 3, len(education_lines))):
                            if any(keyword in education_lines[j].lower() for keyword in college_keywords):
                                # Extract college name (clean it up)
                                college_line = education_lines[j].strip()
                                
                                # Remove degree abbreviations from college name
                                college_line = re.sub(r'\b(B\.?Tech|M\.?Tech|B\.?E\.?|M\.?E\.?|B\.?S\.?c?|M\.?S\.?c?|MBA|BBA)\b', '', college_line, flags=re.IGNORECASE)
                                
                                # Remove years (4 digits with optional range)
                                college_line = re.sub(r'\d{4}[-–—]?\d{0,4}', '', college_line)
                                
                                # Remove GPA/CGPA and scores
                                college_line = re.sub(r'(?:GPA|CGPA|Grade)[\s:]*\d+\.?\d*', '', college_line, flags=re.IGNORECASE)
                                college_line = re.sub(r'\d+\.?\d*\s*(?:GPA|CGPA)', '', college_line, flags=re.IGNORECASE)
                                college_line = re.sub(r'\d+\.?\d+', '', college_line)  # Remove any decimal numbers (likely GPA)
                                
                                # Remove common prefixes
                                college_line = re.sub(r'^at\s+', '', college_line, flags=re.IGNORECASE)
                                college_line = re.sub(r'^from\s+', '', college_line, flags=re.IGNORECASE)
                                
                                # Clean up extra spaces
                                college_line = ' '.join(college_line.split())
                                
                                if college_line and len(college_line) > 5:
                                    edu_entry['college'] = college_line[:100]  # Limit length
                                break
                        
                        # Look for year range (2020-2024, 2020-24, 2020 - 2024, etc.)
                        year_range_patterns = [
                            r'((?:19|20)\d{2})\s*[-–—]\s*((?:19|20)?\d{2})',  # 2020-2024 or 2020-24
                            r'((?:19|20)\d{2})\s+(?:to|TO)\s+((?:19|20)\d{2})',  # 2020 to 2024
                        ]
                        
                        year_found = False
                        # Check current line and next 2 lines for year range
                        for k in range(i, min(i + 3, len(education_lines))):
                            for year_pattern in year_range_patterns:
                                year_match = re.search(year_pattern, education_lines[k])
                                if year_match:
                                    start_year = year_match.group(1)
                                    end_year = year_match.group(2)
                                    
                                    # If end year is 2 digits, convert to 4 digits
                                    if len(end_year) == 2:
                                        # Assume same century as start year
                                        end_year = start_year[:2] + end_year
                                    
                                    edu_entry['year'] = f"{start_year}-{end_year}"
                                    year_found = True
                                    break
                            if year_found:
                                break
                        
                        # If no range found, look for single year
                        if not year_found:
                            for k in range(i, min(i + 3, len(education_lines))):
                                year_match = re.search(r'(19|20)\d{2}', education_lines[k])
                                if year_match:
                                    edu_entry['year'] = year_match.group(0)
                                    break
                        
                        # Look for GPA/CGPA - extract just the number
                        gpa_patterns = [
                            r'(?:GPA|CGPA|Grade)[\s:]*(\d+\.?\d*)',
                            r'(\d+\.?\d*)\s*(?:GPA|CGPA)',
                            r'(\d+\.?\d*)%'
                        ]
                        
                        for k in range(i, min(i + 3, len(education_lines))):
                            for gpa_pattern in gpa_patterns:
                                gpa_match = re.search(gpa_pattern, education_lines[k], re.IGNORECASE)
                                if gpa_match:
                                    gpa_value = gpa_match.group(1)
                                    # Store just the GPA value
                                    edu_entry['gpa'] = gpa_value
                                    break
                            if 'gpa' in edu_entry:
                                break
                        
                        if edu_entry:
                            education.append(edu_entry)
                        break
            
            return education[:5]  # Limit to 5 entries
            
        except Exception as e:
            logger.error(f"Error extracting education: {str(e)}")
            return []
    
    def _extract_experience(self, text: str) -> List[Dict]:
        """Extract work experience"""
        try:
            experience = []
            lines = text.split('\n')
            
            # Find experience section
            exp_start = -1
            for i, line in enumerate(lines):
                if any(keyword in line.lower() for keyword in self.experience_keywords):
                    exp_start = i
                    break
            
            if exp_start == -1:
                return []
            
            # Extract experience entries
            exp_text = '\n'.join(lines[exp_start:exp_start + 30])
            
            # Look for job title and company patterns
            job_pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:at|@)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
            matches = re.findall(job_pattern, exp_text)
            
            for match in matches[:5]:  # Limit to 5 entries
                experience.append({
                    "title": match[0],
                    "company": match[1]
                })
            
            return experience
            
        except Exception as e:
            logger.error(f"Error extracting experience: {str(e)}")
            return []
    
    def _extract_skills(self, text: str) -> List[str]:
        """Extract skills"""
        try:
            skills = []
            lines = text.split('\n')
            
            # Find skills section
            skills_start = -1
            for i, line in enumerate(lines):
                if any(keyword in line.lower() for keyword in self.skills_keywords):
                    skills_start = i
                    break
            
            if skills_start == -1:
                return []
            
            # Extract skills (next 5-10 lines)
            skills_text = '\n'.join(lines[skills_start:skills_start + 10])
            
            # Common tech skills
            common_skills = [
                'Python', 'Java', 'JavaScript', 'C++', 'C#', 'Ruby', 'PHP', 'Swift',
                'React', 'Angular', 'Vue', 'Node.js', 'Django', 'Flask', 'Spring',
                'SQL', 'MongoDB', 'PostgreSQL', 'MySQL', 'Redis',
                'AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes',
                'Git', 'Jenkins', 'CI/CD', 'Agile', 'Scrum'
            ]
            
            for skill in common_skills:
                if re.search(r'\b' + re.escape(skill) + r'\b', skills_text, re.IGNORECASE):
                    skills.append(skill)
            
            return skills[:20]  # Limit to 20 skills
            
        except Exception as e:
            logger.error(f"Error extracting skills: {str(e)}")
            return []
    
    def _extract_certifications(self, text: str) -> List[str]:
        """Extract certification names only"""
        try:
            certifications = []
            lines = text.split('\n')
            
            # Find certification section
            cert_start = -1
            for i, line in enumerate(lines):
                if any(keyword in line.lower() for keyword in self.certification_keywords):
                    cert_start = i
                    break
            
            if cert_start == -1:
                return []
            
            # Extract certifications (next 10 lines after certification header)
            for line in lines[cert_start + 1:cert_start + 11]:
                line = line.strip()
                
                # Skip empty lines and section headers
                if not line or len(line) < 5:
                    continue
                    
                # Skip if it's another section header
                if any(keyword in line.lower() for keyword in self.certification_keywords):
                    continue
                
                # Skip if it looks like a date or year only
                if re.match(r'^\d{4}[-/]\d{2}[-/]\d{2}$', line) or re.match(r'^\d{4}$', line):
                    continue
                
                # Clean up the certification name
                cert_name = line
                # Remove dates at the end (e.g., "AWS Certified - 2023")
                cert_name = re.sub(r'\s*[-–—]\s*\d{4}.*$', '', cert_name)
                cert_name = re.sub(r'\s*\(\d{4}\).*$', '', cert_name)
                cert_name = re.sub(r'\s*\d{4}.*$', '', cert_name)
                cert_name = cert_name.strip()
                
                # Only add if it's a meaningful certification name
                if cert_name and len(cert_name) > 5 and len(cert_name) < 150:
                    certifications.append(cert_name)
            
            return certifications[:10]  # Limit to 10
            
        except Exception as e:
            logger.error(f"Error extracting certifications: {str(e)}")
            return []
    
    def _extract_summary(self, text: str) -> Optional[str]:
        """Extract professional summary"""
        try:
            lines = text.split('\n')
            
            # Look for summary section
            summary_keywords = ['summary', 'objective', 'profile', 'about']
            for i, line in enumerate(lines):
                if any(keyword in line.lower() for keyword in summary_keywords):
                    # Get next 3-5 lines as summary
                    summary_lines = []
                    for j in range(i + 1, min(i + 6, len(lines))):
                        if lines[j].strip():
                            summary_lines.append(lines[j].strip())
                    
                    if summary_lines:
                        return ' '.join(summary_lines)[:500]  # Limit to 500 chars
            
            return None
        except Exception as e:
            logger.error(f"Error extracting summary: {str(e)}")
            return None
    
    def _calculate_experience_years(self, text: str) -> Optional[int]:
        """Calculate total years of experience"""
        try:
            # Look for patterns like "5 years", "5+ years", "5-7 years"
            patterns = [
                r'(\d+)\+?\s*years?\s+(?:of\s+)?experience',
                r'experience\s*:\s*(\d+)\+?\s*years?'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    return int(match.group(1))
            
            return None
        except Exception as e:
            logger.error(f"Error calculating experience years: {str(e)}")
            return None
    
    def _empty_parsed_data(self) -> Dict:
        """Return empty parsed data structure"""
        return {
            "name": None,
            "email": None,
            "phone": None,
            "linkedin": None,
            "github": None,
            "education": [],
            "experience": [],
            "skills": [],
            "certifications": [],
            "summary": None,
            "total_experience_years": None,
            "extracted_text": "",
            "parsed_at": datetime.utcnow().isoformat()
        }
    
    def _extract_education_fallback(self, text: str) -> List[Dict]:
        """
        Fallback method to extract education when no clear section is found.
        Searches for degree patterns anywhere in the document.
        """
        try:
            education = []
            lines = text.split('\n')
            
            # More comprehensive degree patterns
            degree_patterns = [
                r'\b(B\.?\s?Tech|B\.?\s?E\.?)\s+(?:in\s+)?([A-Za-z\s&]+)',
                r'\b(M\.?\s?Tech|M\.?\s?E\.?)\s+(?:in\s+)?([A-Za-z\s&]+)',
                r'\b(B\.?\s?S\.?c?|M\.?\s?S\.?c?)\s+(?:in\s+)?([A-Za-z\s&]+)',
                r'\b(MBA|BBA|MCA|BCA|PhD|Doctorate)',
                r'\b(Bachelor|Master)\s+of\s+([A-Za-z\s&]+)',
                r'\b(Diploma)\s+in\s+([A-Za-z\s&]+)',
            ]
            
            university_keywords = ['university', 'college', 'institute', 'school', 'academy']
            
            for i, line in enumerate(lines):
                for pattern in degree_patterns:
                    match = re.search(pattern, line, re.IGNORECASE)
                    if match:
                        edu_entry = {}
                        
                        # Extract degree
                        if len(match.groups()) >= 2 and match.group(2):
                            degree = f"{match.group(1)} {match.group(2).strip()}"
                        else:
                            degree = match.group(1).strip()
                        
                        # Clean up degree name
                        degree = re.sub(r'\s+', ' ', degree)
                        degree = degree[:100]  # Limit length
                        edu_entry['degree'] = degree
                        
                        # Look for university in nearby lines
                        for j in range(max(0, i-2), min(len(lines), i+3)):
                            if any(kw in lines[j].lower() for kw in university_keywords):
                                college = lines[j].strip()
                                # Clean up
                                college = re.sub(r'\d{4}[-–—]?\d{0,4}', '', college)
                                college = re.sub(r'(?:GPA|CGPA)[\s:]*\d+\.?\d*', '', college, flags=re.IGNORECASE)
                                college = ' '.join(college.split())
                                if len(college) > 5:
                                    edu_entry['college'] = college[:100]
                                break
                        
                        # Look for years
                        for j in range(max(0, i-1), min(len(lines), i+3)):
                            year_match = re.search(r'((?:19|20)\d{2})\s*[-–—]\s*((?:19|20)?\d{2})', lines[j])
                            if year_match:
                                edu_entry['year'] = f"{year_match.group(1)}-{year_match.group(2)}"
                                break
                        
                        if edu_entry and 'degree' in edu_entry:
                            education.append(edu_entry)
                            logger.info(f"Fallback: Found education - {edu_entry.get('degree')}")
                            break  # Only one degree per line
            
            logger.info(f"Fallback extraction found {len(education)} education entries")
            return education
            
        except Exception as e:
            logger.error(f"Error in fallback education extraction: {str(e)}")
            return []
