import pytest
from services.jd_matcher import JDMatcher


class TestJDMatcher:
    """Test cases for JD matching functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.matcher = JDMatcher()

    def test_jd_matcher_initialization(self):
        """Test JD matcher initializes correctly"""
        assert self.matcher is not None
        assert hasattr(self.matcher, 'skill_categories')
        assert hasattr(self.matcher, 'education_keywords')

    def test_extract_keywords_programming(self):
        """Test extraction of programming keywords"""
        text = "Experienced in Python, Java, and JavaScript development"
        keywords = self.matcher._extract_keywords(text)
        
        assert 'python' in keywords['programming']
        assert 'java' in keywords['programming']
        assert 'javascript' in keywords['programming']
        assert len(keywords['all_skills']) >= 3

    def test_extract_keywords_web_technologies(self):
        """Test extraction of web technology keywords"""
        text = "Proficient in React, Node.js, and Django frameworks"
        keywords = self.matcher._extract_keywords(text)
        
        assert 'react' in keywords['web']
        assert 'node.js' in keywords['web']
        assert 'django' in keywords['web']

    def test_extract_years_experience(self):
        """Test extraction of years of experience"""
        test_cases = [
            ("5 years of experience in software development", 5),
            ("Experience of 3+ years required", 3),
            ("10 years experience", 10),
            ("2 yrs in Python", 2),
            ("No specific experience mentioned", None)
        ]
        
        for text, expected in test_cases:
            result = self.matcher._extract_years_experience(text)
            assert result == expected, f"Failed for: {text}"

    def test_skills_match_perfect(self):
        """Test perfect skills match"""
        jd_text = "Looking for Python and JavaScript developer"
        resume_text = "Expert in Python and JavaScript with 5 years experience"
        
        result = self.matcher.match_resume_with_jd(resume_text, jd_text)
        
        assert result['skills_match'] >= 90.0
        assert 'python' in result['matched_skills']
        assert 'javascript' in result['matched_skills']

    def test_skills_match_partial(self):
        """Test partial skills match"""
        jd_text = "Need Python, Java, React, and AWS experience"
        resume_text = "Experienced in Python and Java development"
        
        result = self.matcher.match_resume_with_jd(resume_text, jd_text)
        
        assert result['skills_match'] < 100.0
        assert 'python' in result['matched_skills']
        assert 'java' in result['matched_skills']
        assert 'react' in result['missing_skills']
        assert 'aws' in result['missing_skills']

    def test_experience_match_exact(self):
        """Test experience matching with exact match"""
        jd_text = "5 years of experience required"
        resume_text = "5 years of software development experience"
        
        result = self.matcher.match_resume_with_jd(resume_text, jd_text)
        
        assert result['experience_match'] >= 50.0

    def test_experience_match_exceeds(self):
        """Test experience matching when candidate exceeds requirement"""
        jd_text = "3 years of experience required"
        resume_text = "8 years of professional experience"
        
        result = self.matcher.match_resume_with_jd(resume_text, jd_text)
        
        assert result['experience_match'] >= 50.0

    def test_experience_match_below(self):
        """Test experience matching when candidate is below requirement"""
        jd_text = "5 years of experience required"
        resume_text = "2 years of experience"
        
        result = self.matcher.match_resume_with_jd(resume_text, jd_text)
        
        assert result['experience_match'] < 80.0

    def test_education_match_bachelor(self):
        """Test education matching for bachelor's degree"""
        jd_text = "Bachelor's degree in Computer Science required"
        resume_text = "B.Tech in Computer Science from XYZ University"
        
        result = self.matcher.match_resume_with_jd(resume_text, jd_text)
        
        assert result['education_match'] >= 50.0

    def test_education_match_higher_degree(self):
        """Test education matching when candidate has higher degree"""
        jd_text = "Bachelor's degree required"
        resume_text = "Master's degree in Computer Science"
        
        result = self.matcher.match_resume_with_jd(resume_text, jd_text)
        
        assert result['education_match'] >= 70.0

    def test_overall_match_calculation(self):
        """Test overall match score calculation"""
        jd_text = """
        Looking for a Python developer with 3 years of experience.
        Bachelor's degree in Computer Science required.
        Skills: Python, Django, PostgreSQL, AWS
        """
        
        resume_text = """
        Software Engineer with 4 years of experience in Python development.
        B.Tech in Computer Science.
        Skills: Python, Django, PostgreSQL, React, JavaScript
        """
        
        result = self.matcher.match_resume_with_jd(resume_text, jd_text)
        
        assert 0 <= result['overall_match'] <= 100
        assert 0 <= result['skills_match'] <= 100
        assert 0 <= result['experience_match'] <= 100
        assert 0 <= result['education_match'] <= 100
        assert isinstance(result['matched_skills'], list)
        assert isinstance(result['missing_skills'], list)
        assert isinstance(result['details'], list)

    def test_match_with_no_jd_requirements(self):
        """Test matching when JD has minimal requirements"""
        jd_text = "Looking for a software developer"
        resume_text = "Experienced Python developer with 5 years experience"
        
        result = self.matcher.match_resume_with_jd(resume_text, jd_text)
        
        # Should still return valid scores
        assert result['overall_match'] > 0
        assert isinstance(result['details'], list)

    def test_match_with_empty_resume(self):
        """Test matching with minimal resume content"""
        jd_text = "Python developer with 5 years experience needed"
        resume_text = "Software developer"
        
        result = self.matcher.match_resume_with_jd(resume_text, jd_text)
        
        # Should handle gracefully
        assert result['overall_match'] >= 0
        assert len(result['missing_skills']) > 0

    def test_matched_skills_list(self):
        """Test that matched skills are correctly identified"""
        jd_text = "Python, Java, React, AWS"
        resume_text = "Python and React expert"
        
        result = self.matcher.match_resume_with_jd(resume_text, jd_text)
        
        assert 'python' in result['matched_skills']
        assert 'react' in result['matched_skills']
        assert 'java' not in result['matched_skills']

    def test_missing_skills_list(self):
        """Test that missing skills are correctly identified"""
        jd_text = "Python, Java, React, AWS required"
        resume_text = "Python developer"
        
        result = self.matcher.match_resume_with_jd(resume_text, jd_text)
        
        assert 'java' in result['missing_skills']
        assert 'react' in result['missing_skills']
        assert 'aws' in result['missing_skills']

    def test_details_generation(self):
        """Test that detailed feedback is generated"""
        jd_text = "Python developer with 3 years experience"
        resume_text = "Python expert with 5 years experience"
        
        result = self.matcher.match_resume_with_jd(resume_text, jd_text)
        
        assert len(result['details']) > 0
        assert any('skills' in detail.lower() for detail in result['details'])

    def test_case_insensitive_matching(self):
        """Test that matching is case-insensitive"""
        jd_text = "PYTHON and JAVA required"
        resume_text = "python and java expert"
        
        result = self.matcher.match_resume_with_jd(resume_text, jd_text)
        
        assert 'python' in result['matched_skills']
        assert 'java' in result['matched_skills']

    def test_multiple_skill_categories(self):
        """Test matching across multiple skill categories"""
        jd_text = "Python, React, AWS, PostgreSQL, Machine Learning"
        resume_text = "Python, React, AWS, PostgreSQL, Machine Learning expert"
        
        result = self.matcher.match_resume_with_jd(resume_text, jd_text)
        
        assert result['skills_match'] >= 90.0
        assert len(result['matched_skills']) >= 5
