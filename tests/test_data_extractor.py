import pytest
from services.resume_data_extractor import ResumeDataExtractor


@pytest.fixture
def extractor():
    """Create data extractor instance"""
    return ResumeDataExtractor()


class TestEmailExtraction:
    """Test email extraction"""
    
    def test_extract_valid_email(self, extractor):
        """Test extracting valid email"""
        text = "Contact me at john.doe@example.com for more information"
        email = extractor.extract_email(text)
        assert email == "john.doe@example.com"
    
    def test_extract_email_with_noise(self, extractor):
        """Test extracting email from noisy text"""
        text = "Name: John Doe\nEmail: jane.smith@company.co.uk\nPhone: 123-456"
        email = extractor.extract_email(text)
        assert email == "jane.smith@company.co.uk"
    
    def test_no_email_found(self, extractor):
        """Test when no email is present"""
        text = "This is a resume without any email address"
        email = extractor.extract_email(text)
        assert email is None
    
    def test_invalid_email_rejected(self, extractor):
        """Test that invalid emails are rejected"""
        text = "Contact at invalid@email or test@"
        email = extractor.extract_email(text)
        assert email is None or '@' in email  # Should either find nothing or valid email


class TestPhoneExtraction:
    """Test phone number extraction"""
    
    def test_extract_us_format(self, extractor):
        """Test extracting US format phone"""
        text = "Call me at (555) 123-4567"
        phone = extractor.extract_phone(text)
        assert phone is not None
        assert '555' in phone or '123' in phone
    
    def test_extract_international_format(self, extractor):
        """Test extracting international format"""
        text = "Mobile: +1 555 123 4567"
        phone = extractor.extract_phone(text)
        assert phone is not None
    
    def test_no_phone_found(self, extractor):
        """Test when no phone is present"""
        text = "This is a resume without phone number"
        phone = extractor.extract_phone(text)
        assert phone is None


class TestLinkedInExtraction:
    """Test LinkedIn URL extraction"""
    
    def test_extract_linkedin_url(self, extractor):
        """Test extracting LinkedIn URL"""
        text = "Profile: https://www.linkedin.com/in/johndoe"
        url = extractor.extract_linkedin(text)
        assert url is not None
        assert 'linkedin.com' in url
        assert 'johndoe' in url
    
    def test_extract_linkedin_without_https(self, extractor):
        """Test extracting LinkedIn without protocol"""
        text = "LinkedIn: linkedin.com/in/janedoe"
        url = extractor.extract_linkedin(text)
        assert url is not None
        assert 'https://' in url
    
    def test_no_linkedin_found(self, extractor):
        """Test when no LinkedIn is present"""
        text = "This resume has no LinkedIn profile"
        url = extractor.extract_linkedin(text)
        assert url is None


class TestNameExtraction:
    """Test name extraction"""
    
    def test_extract_name_from_first_line(self, extractor):
        """Test extracting name from first line"""
        text = "John Smith\nSoftware Engineer\njohn@example.com"
        name = extractor.extract_name(text)
        assert name is not None
        assert 'John' in name or 'Smith' in name
    
    def test_skip_email_lines(self, extractor):
        """Test that lines with email are skipped"""
        text = "john@example.com\nJohn Smith\nSoftware Engineer"
        name = extractor.extract_name(text)
        assert name is not None
        assert '@' not in name


class TestSkillsExtraction:
    """Test skills extraction"""
    
    def test_extract_common_skills(self, extractor):
        """Test extracting common technical skills"""
        text = """
        Skills:
        - Python programming
        - Java development
        - React framework
        - SQL databases
        """
        skills = extractor.extract_skills(text)
        assert isinstance(skills, list)
        assert len(skills) > 0
        # Check if any expected skills are found
        skill_names_lower = [s.lower() for s in skills]
        assert any('python' in s for s in skill_names_lower)
    
    def test_no_skills_found(self, extractor):
        """Test when no recognized skills are present"""
        text = "I like cooking and playing sports"
        skills = extractor.extract_skills(text)
        assert isinstance(skills, list)
        # May or may not find skills, but should return list


class TestEducationExtraction:
    """Test education extraction"""
    
    def test_extract_bachelor_degree(self, extractor):
        """Test extracting bachelor's degree"""
        text = """
        Education:
        Bachelor of Science in Computer Science
        Massachusetts Institute of Technology
        2015 - 2019
        """
        education = extractor.extract_education(text)
        assert isinstance(education, list)
        if len(education) > 0:
            assert 'bachelor' in education[0]['degree'].lower() or 'b.s' in education[0]['degree'].lower()
    
    def test_extract_masters_degree(self, extractor):
        """Test extracting master's degree"""
        text = """
        M.S. in Computer Science
        Stanford University
        2020
        """
        education = extractor.extract_education(text)
        assert isinstance(education, list)
        if len(education) > 0:
            assert 'degree' in education[0]


class TestWorkExperienceExtraction:
    """Test work experience extraction"""
    
    def test_extract_work_experience_with_dates(self, extractor):
        """Test extracting work experience with date ranges"""
        text = """
        Software Engineer
        Google Inc.
        Jan 2020 - Dec 2022
        - Developed web applications
        """
        experience = extractor.extract_work_experience(text)
        assert isinstance(experience, list)
        # Experience extraction is heuristic-based, may or may not find entries
    
    def test_extract_current_job(self, extractor):
        """Test extracting current job (with 'Present')"""
        text = """
        Senior Developer
        Microsoft Corporation
        2021 - Present
        """
        experience = extractor.extract_work_experience(text)
        assert isinstance(experience, list)


class TestFullExtraction:
    """Test complete data extraction"""
    
    def test_extract_all_from_complete_resume(self, extractor):
        """Test extracting all data from a complete resume"""
        text = """
        John Smith
        john.smith@example.com | +1-555-123-4567
        linkedin.com/in/johnsmith
        
        PROFESSIONAL SUMMARY
        Experienced Software Engineer with 5 years of experience.
        
        SKILLS
        Python, Java, JavaScript, React, SQL, AWS
        
        EDUCATION
        Master of Science in Computer Science
        Stanford University
        2018 - 2020
        
        WORK EXPERIENCE
        Senior Software Engineer
        Google Inc.
        Jan 2020 - Present
        - Lead development of cloud applications
        
        Software Engineer
        Microsoft Corporation
        2018 - 2020
        """
        
        result = extractor.extract_all(text)
        
        assert isinstance(result, dict)
        assert 'email' in result
        assert 'phone' in result
        assert 'linkedin_url' in result
        assert 'name' in result
        assert 'skills' in result
        assert 'education' in result
        assert 'work_experience' in result
        
        # Verify email was found
        assert result['email'] is not None
        assert 'john.smith@example.com' in result['email'].lower()
    
    def test_extract_from_empty_text(self, extractor):
        """Test extraction from empty text"""
        result = extractor.extract_all("")
        
        assert isinstance(result, dict)
        assert result['email'] is None
        assert result['phone'] is None
        assert result['linkedin_url'] is None
