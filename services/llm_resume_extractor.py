"""
LLM-based Resume Extraction using Google Gemini or OpenAI
Provides structured extraction with high accuracy across all resume formats
"""
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import re
from services.llm_usage_tracker import get_tracker

logger = logging.getLogger(__name__)

# Try importing both LLM providers
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("Google Gemini not available. Install: pip install google-generativeai")

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI not available. Install: pip install openai")


class LLMResumeExtractor:
    """Extract structured data from resumes using LLM"""
    
    def __init__(self, provider: str = "gemini", api_key: Optional[str] = None, user_token: Optional[str] = None):
        """
        Initialize LLM extractor
        
        Args:
            provider: "gemini" or "openai"
            api_key: System API key (fallback)
            user_token: User's OAuth token (preferred for quota distribution)
        """
        self.provider = provider.lower()
        self.api_key = api_key
        self.user_token = user_token
        
        # Configure provider
        if self.provider == "gemini" and GEMINI_AVAILABLE:
            genai.configure(api_key=user_token or api_key)
            # Use Gemini 2.0 Flash (latest, fastest, free tier)
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
            logger.info(f"✅ Gemini 2.0 Flash initialized with {'user token' if user_token else 'system key'}")
        elif self.provider == "openai" and OPENAI_AVAILABLE:
            openai.api_key = user_token or api_key
            self.model_name = "gpt-4o-mini"  # Fast and cheap
            logger.info(f"✅ OpenAI initialized with {'user token' if user_token else 'system key'}")
        else:
            raise ValueError(f"Provider '{provider}' not available or not installed")
    
    def extract(self, resume_text: str) -> Dict[str, Any]:
        """
        Extract structured data from resume text
        
        Returns:
            {
                "name": str,
                "email": str,
                "phone": str,
                "linkedin_url": str,
                "github_url": str,
                "portfolio_url": str,
                "location": str,
                "summary": str,
                "work_experience": [...],
                "education": [...],
                "skills": [...],
                "certifications": [...],
                "languages": [...]
            }
        """
        try:
            logger.info(f"🤖 Starting LLM extraction with {self.provider}")
            
            if self.provider == "gemini":
                return self._extract_with_gemini(resume_text)
            elif self.provider == "openai":
                return self._extract_with_openai(resume_text)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
                
        except Exception as e:
            logger.error(f"❌ LLM extraction failed: {e}")
            raise
    
    def _extract_with_gemini(self, resume_text: str) -> Dict[str, Any]:
        """Extract using Google Gemini"""
        
        # Check quota before making request
        tracker = get_tracker()
        can_proceed, warning = tracker.can_make_request("gemini")
        
        if not can_proceed:
            logger.error(f"❌ Gemini quota exceeded: {warning}")
            raise Exception(f"Gemini quota exceeded: {warning}")
        
        if warning:
            logger.warning(warning)
        
        prompt = self._build_extraction_prompt(resume_text)
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.1,  # Low temperature for consistent extraction
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": 4096,
                }
            )
            
            # Track usage
            tokens_used = response.usage_metadata.total_token_count if hasattr(response, 'usage_metadata') else 0
            tracker.track_request("gemini", success=True, tokens_used=tokens_used)
            
            # Extract JSON from response
            result_text = response.text.strip()
            
            # Remove markdown code blocks if present
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.startswith("```"):
                result_text = result_text[3:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]
            
            result_text = result_text.strip()
            
            # Parse JSON
            extracted_data = json.loads(result_text)
            
            logger.info(f"✅ Gemini extraction successful: {extracted_data.get('name', 'Unknown')}")
            return extracted_data
            
        except json.JSONDecodeError as e:
            tracker.track_request("gemini", success=False)
            logger.error(f"❌ Failed to parse Gemini response as JSON: {e}")
            logger.error(f"Response text: {response.text[:500]}")
            raise
        except Exception as e:
            tracker.track_request("gemini", success=False)
            logger.error(f"❌ Gemini API error: {e}")
            raise
    
    def _extract_with_openai(self, resume_text: str) -> Dict[str, Any]:
        """Extract using OpenAI"""
        
        prompt = self._build_extraction_prompt(resume_text)
        
        try:
            response = openai.ChatCompletion.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are an expert resume parser. Extract structured information and return ONLY valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=4096
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.startswith("```"):
                result_text = result_text[3:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]
            
            result_text = result_text.strip()
            
            # Parse JSON
            extracted_data = json.loads(result_text)
            
            logger.info(f"✅ OpenAI extraction successful: {extracted_data.get('name', 'Unknown')}")
            return extracted_data
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse OpenAI response as JSON: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ OpenAI API error: {e}")
            raise
    
    def _build_extraction_prompt(self, resume_text: str) -> str:
        """Build the extraction prompt"""
        
        return f"""
Extract structured information from this resume and return ONLY valid JSON (no markdown, no explanations).

IMPORTANT RULES:
1. Extract ACTUAL names, not skills or technical terms (e.g., "Good SQL" is NOT a name)
2. For work experience, extract company names carefully - ignore OCR artifacts
3. Calculate duration_months accurately from start_date and end_date
4. If a field is not found, use null (not empty string)
5. For dates, use MM/YYYY format
6. Return ONLY the JSON object, nothing else

JSON Schema:
{{
  "name": "Full Name (ACTUAL person name, not skills)",
  "email": "email@example.com or null",
  "phone": "phone number or null",
  "linkedin_url": "LinkedIn URL or null",
  "github_url": "GitHub URL or null",
  "portfolio_url": "Portfolio URL or null",
  "location": "City, State/Country or null",
  "summary": "Professional summary text or null",
  "work_experience": [
    {{
      "company": "Company Name (ignore OCR garbage)",
      "title": "Job Title",
      "location": "City, State or null",
      "start_date": "MM/YYYY",
      "end_date": "MM/YYYY or Present",
      "duration_months": 12,
      "is_current": false,
      "responsibilities": ["responsibility 1", "responsibility 2"],
      "description": "Brief description"
    }}
  ],
  "education": [
    {{
      "institution": "University/College Name",
      "degree": "Degree Name",
      "field_of_study": "Major/Field",
      "start_date": "YYYY or null",
      "end_date": "YYYY or null",
      "grade": "GPA/Grade or null",
      "location": "City, State or null"
    }}
  ],
  "skills": [
    {{
      "category": "Technical/Soft/Language",
      "name": "Skill Name",
      "proficiency": "Beginner/Intermediate/Advanced/Expert or null"
    }}
  ],
  "certifications": [
    {{
      "name": "Certification Name",
      "issuer": "Issuing Organization",
      "date": "MM/YYYY or null",
      "expiry_date": "MM/YYYY or null",
      "credential_id": "ID or null"
    }}
  ],
  "languages": [
    {{
      "language": "Language Name",
      "proficiency": "Native/Fluent/Intermediate/Basic"
    }}
  ],
  "projects": [
    {{
      "name": "Project Name",
      "description": "Brief description",
      "technologies": ["tech1", "tech2"],
      "url": "Project URL or null"
    }}
  ]
}}

Resume Text:
{resume_text}

Return ONLY the JSON object:
"""
    
    def validate_extraction(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean extracted data"""
        
        # Ensure required fields exist
        required_fields = ["name", "email", "phone", "work_experience", "education", "skills"]
        for field in required_fields:
            if field not in data:
                data[field] = None if field in ["name", "email", "phone"] else []
        
        # Validate name (reject skill-like names)
        if data.get("name"):
            name_lower = data["name"].lower()
            skill_keywords = ['sql', 'java', 'python', 'react', 'good', 'excellent', 'strong']
            if any(skill in name_lower for skill in skill_keywords):
                logger.warning(f"⚠️ Rejecting skill-like name: {data['name']}")
                data["name"] = None
        
        # Calculate total experience (handle None values safely)
        total_months = 0
        for exp in data.get("work_experience", []):
            duration = exp.get("duration_months")
            if duration is not None and isinstance(duration, (int, float)):
                total_months += int(duration)
        
        data["total_experience_months"] = total_months
        data["total_experience_years"] = round(total_months / 12, 1) if total_months > 0 else 0
        
        return data


# Factory function
def create_llm_extractor(provider: str = "gemini", api_key: Optional[str] = None, user_token: Optional[str] = None) -> LLMResumeExtractor:
    """Create LLM extractor instance"""
    return LLMResumeExtractor(provider=provider, api_key=api_key, user_token=user_token)
