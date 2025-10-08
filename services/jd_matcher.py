import re
import logging
from typing import Dict, List, Set, Any
from collections import Counter

logger = logging.getLogger(__name__)


class JDMatcher:
    """Matches resumes with job descriptions using NLP and keyword analysis"""

    def __init__(self):
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
            logger.warning("NLTK not available for advanced matching")

        # Common skill categories and keywords
        self.skill_categories = {
            'programming': [
                'python', 'java', 'javascript', 'c++', 'c#', 'ruby', 'php', 'swift',
                'kotlin', 'go', 'rust', 'typescript', 'scala', 'perl', 'r', 'matlab'
            ],
            'web': [
                'html', 'css', 'react', 'angular', 'vue', 'node.js', 'express',
                'django', 'flask', 'fastapi', 'spring', 'asp.net', 'jquery'
            ],
            'database': [
                'sql', 'mysql', 'postgresql', 'mongodb', 'oracle', 'redis',
                'cassandra', 'dynamodb', 'sqlite', 'mariadb', 'nosql'
            ],
            'cloud': [
                'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform',
                'jenkins', 'ci/cd', 'devops', 'cloud computing'
            ],
            'data_science': [
                'machine learning', 'deep learning', 'ai', 'data analysis',
                'pandas', 'numpy', 'scikit-learn', 'tensorflow', 'pytorch',
                'nlp', 'computer vision', 'statistics'
            ],
            'soft_skills': [
                'leadership', 'communication', 'teamwork', 'problem solving',
                'analytical', 'creative', 'adaptable', 'organized'
            ]
        }

        # Education keywords
        self.education_keywords = [
            'bachelor', 'master', 'phd', 'doctorate', 'degree', 'diploma',
            'certification', 'certified', 'graduate', 'undergraduate',
            'b.tech', 'm.tech', 'b.e', 'm.e', 'mba', 'bca', 'mca',
            'computer science', 'engineering', 'information technology'
        ]

        # Experience indicators
        self.experience_keywords = [
            'years', 'experience', 'worked', 'developed', 'managed', 'led',
            'designed', 'implemented', 'created', 'built', 'maintained'
        ]

    def match_resume_with_jd(self, resume_text: str, jd_text: str) -> Dict[str, Any]:
        """
        Match resume with job description and calculate relevance scores
        
        Args:
            resume_text: Extracted text from resume
            jd_text: Job description text
            
        Returns:
            Dictionary with matching scores and details
        """
        # Extract keywords from both texts
        jd_keywords = self._extract_keywords(jd_text)
        resume_keywords = self._extract_keywords(resume_text)

        # Calculate individual scores
        skills_score = self._calculate_skills_match(jd_keywords, resume_keywords)
        experience_score = self._calculate_experience_match(resume_text, jd_text)
        education_score = self._calculate_education_match(resume_text, jd_text)

        # Calculate overall match (weighted average)
        weights = {
            'skills': 0.50,      # 50% weight on skills
            'experience': 0.30,  # 30% weight on experience
            'education': 0.20    # 20% weight on education
        }

        overall_match = (
            skills_score * weights['skills'] +
            experience_score * weights['experience'] +
            education_score * weights['education']
        )

        # Generate detailed feedback
        matched_skills = self._get_matched_skills(jd_keywords, resume_keywords)
        missing_skills = self._get_missing_skills(jd_keywords, resume_keywords)

        return {
            'overall_match': round(overall_match, 1),
            'skills_match': round(skills_score, 1),
            'experience_match': round(experience_score, 1),
            'education_match': round(education_score, 1),
            'matched_skills': matched_skills,
            'missing_skills': missing_skills,
            'details': self._generate_match_details(
                skills_score, experience_score, education_score,
                matched_skills, missing_skills
            )
        }

    def _extract_keywords(self, text: str) -> Dict[str, Set[str]]:
        """Extract categorized keywords from text"""
        text_lower = text.lower()
        keywords = {
            'programming': set(),
            'web': set(),
            'database': set(),
            'cloud': set(),
            'data_science': set(),
            'soft_skills': set(),
            'all_skills': set()
        }

        # Extract skills by category
        for category, skill_list in self.skill_categories.items():
            for skill in skill_list:
                # Use word boundaries to avoid partial matches
                pattern = r'\b' + re.escape(skill.lower()) + r'\b'
                if re.search(pattern, text_lower):
                    keywords[category].add(skill)
                    keywords['all_skills'].add(skill)

        return keywords

    def _calculate_skills_match(self, jd_keywords: Dict[str, Set[str]], 
                                resume_keywords: Dict[str, Set[str]]) -> float:
        """Calculate skills matching score"""
        jd_skills = jd_keywords['all_skills']
        resume_skills = resume_keywords['all_skills']

        if not jd_skills:
            return 75.0  # Default if no specific skills in JD

        # Calculate match percentage
        matched_skills = jd_skills.intersection(resume_skills)
        match_percentage = (len(matched_skills) / len(jd_skills)) * 100

        # Bonus for extra skills not in JD
        extra_skills = resume_skills - jd_skills
        bonus = min(len(extra_skills) * 2, 10)  # Up to 10% bonus

        return min(match_percentage + bonus, 100.0)

    def _calculate_experience_match(self, resume_text: str, jd_text: str) -> float:
        """Calculate experience matching score"""
        # Extract years of experience from JD
        jd_years = self._extract_years_experience(jd_text)
        resume_years = self._extract_years_experience(resume_text)

        if jd_years is None:
            # No specific experience requirement
            return 80.0 if resume_years else 60.0

        if resume_years is None:
            # Can't determine resume experience
            return 50.0

        # Calculate match based on experience gap
        if resume_years >= jd_years:
            # Meets or exceeds requirement
            excess = resume_years - jd_years
            if excess <= 2:
                return 100.0  # Perfect match
            elif excess <= 5:
                return 95.0   # Slightly overqualified
            else:
                return 85.0   # Significantly overqualified
        else:
            # Below requirement
            gap = jd_years - resume_years
            if gap <= 1:
                return 80.0   # Close enough
            elif gap <= 2:
                return 60.0   # Somewhat below
            else:
                return 40.0   # Significantly below

    def _extract_years_experience(self, text: str) -> int:
        """Extract years of experience from text"""
        # Patterns to match experience mentions
        patterns = [
            r'(\d+)\+?\s*(?:years?|yrs?)\s+(?:of\s+)?experience',
            r'experience\s+(?:of\s+)?(\d+)\+?\s*(?:years?|yrs?)',
            r'(\d+)\+?\s*(?:years?|yrs?)\s+(?:in|with)',
        ]

        years = []
        for pattern in patterns:
            matches = re.findall(pattern, text.lower())
            years.extend([int(match) for match in matches])

        return max(years) if years else None

    def _calculate_education_match(self, resume_text: str, jd_text: str) -> float:
        """Calculate education matching score"""
        resume_lower = resume_text.lower()
        jd_lower = jd_text.lower()

        # Check for education keywords in both texts
        jd_education = [kw for kw in self.education_keywords if kw in jd_lower]
        resume_education = [kw for kw in self.education_keywords if kw in resume_lower]

        if not jd_education:
            # No specific education requirement
            return 85.0 if resume_education else 70.0

        # Calculate match percentage
        matched = set(jd_education).intersection(set(resume_education))
        match_percentage = (len(matched) / len(jd_education)) * 100

        # Check for degree levels
        degree_hierarchy = {
            'phd': 4, 'doctorate': 4,
            'master': 3, 'm.tech': 3, 'm.e': 3, 'mba': 3, 'mca': 3,
            'bachelor': 2, 'b.tech': 2, 'b.e': 2, 'bca': 2,
            'diploma': 1
        }

        jd_degree_level = max([degree_hierarchy.get(kw, 0) for kw in jd_education], default=0)
        resume_degree_level = max([degree_hierarchy.get(kw, 0) for kw in resume_education], default=0)

        if resume_degree_level >= jd_degree_level:
            return min(match_percentage + 20, 100.0)  # Bonus for meeting degree requirement
        else:
            return max(match_percentage - 20, 30.0)   # Penalty for not meeting requirement

    def _get_matched_skills(self, jd_keywords: Dict[str, Set[str]], 
                           resume_keywords: Dict[str, Set[str]]) -> List[str]:
        """Get list of matched skills"""
        jd_skills = jd_keywords['all_skills']
        resume_skills = resume_keywords['all_skills']
        matched = jd_skills.intersection(resume_skills)
        return sorted(list(matched))

    def _get_missing_skills(self, jd_keywords: Dict[str, Set[str]], 
                           resume_keywords: Dict[str, Set[str]]) -> List[str]:
        """Get list of skills in JD but missing from resume"""
        jd_skills = jd_keywords['all_skills']
        resume_skills = resume_keywords['all_skills']
        missing = jd_skills - resume_skills
        return sorted(list(missing))

    def _generate_match_details(self, skills_score: float, experience_score: float,
                                education_score: float, matched_skills: List[str],
                                missing_skills: List[str]) -> List[str]:
        """Generate detailed matching feedback"""
        details = []

        # Skills feedback
        if skills_score >= 80:
            details.append(f"✓ Strong skills match - {len(matched_skills)} key skills found")
        elif skills_score >= 60:
            details.append(f"○ Moderate skills match - {len(matched_skills)} skills found")
        else:
            details.append(f"✗ Limited skills match - only {len(matched_skills)} skills found")

        if missing_skills:
            if len(missing_skills) <= 3:
                details.append(f"Missing skills: {', '.join(missing_skills[:3])}")
            else:
                details.append(f"Missing {len(missing_skills)} skills including: {', '.join(missing_skills[:3])}")

        # Experience feedback
        if experience_score >= 80:
            details.append("✓ Experience level meets or exceeds requirements")
        elif experience_score >= 60:
            details.append("○ Experience level is close to requirements")
        else:
            details.append("✗ Experience level below requirements")

        # Education feedback
        if education_score >= 80:
            details.append("✓ Education qualifications match requirements")
        elif education_score >= 60:
            details.append("○ Education qualifications partially match")
        else:
            details.append("✗ Education qualifications may not meet requirements")

        return details
