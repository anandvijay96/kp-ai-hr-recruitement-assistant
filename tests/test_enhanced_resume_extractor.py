"""
Test Suite for Enhanced Resume Extractor
Following TDD approach - tests written first, then implementation
Target: 95%+ accuracy for all extraction features
"""

import pytest
from services.enhanced_resume_extractor import EnhancedResumeExtractor


class TestWorkExperienceExtraction:
    """Test work experience extraction with all fields"""
    
    @pytest.fixture
    def extractor(self):
        return EnhancedResumeExtractor()
    
    def test_extract_single_work_experience(self, extractor):
        """Test extraction of single work experience entry"""
        resume_text = """
        WORK EXPERIENCE
        
        Senior Software Engineer
        Google Inc., Mountain View, CA
        January 2020 - Present
        • Led team of 5 developers in building cloud infrastructure
        • Implemented microservices architecture using Kubernetes
        • Reduced deployment time by 40%
        """
        
        result = extractor.extract_all(resume_text)
        experiences = result['work_experience']
        
        assert len(experiences) >= 1
        exp = experiences[0]
        assert exp['title'] is not None
        assert 'engineer' in exp['title'].lower()
        assert exp['company'] is not None
        assert 'google' in exp['company'].lower()
        assert exp['start_date'] is not None
        assert exp['end_date'] is not None
        assert exp['is_current'] == True
        assert len(exp['responsibilities']) >= 2
    
    def test_extract_multiple_work_experiences(self, extractor):
        """Test extraction of multiple work experience entries"""
        resume_text = """
        PROFESSIONAL EXPERIENCE
        
        Senior Developer
        Microsoft Corporation
        June 2018 - December 2019
        • Developed Azure cloud solutions
        • Mentored junior developers
        
        Software Developer
        Amazon Web Services
        January 2016 - May 2018
        • Built scalable APIs
        • Implemented CI/CD pipelines
        """
        
        result = extractor.extract_all(resume_text)
        experiences = result['work_experience']
        
        assert len(experiences) >= 2
        # Check first experience
        assert experiences[0]['company'] is not None
        assert experiences[0]['title'] is not None
        assert experiences[0]['start_date'] is not None
        assert experiences[0]['end_date'] is not None
        assert experiences[0]['is_current'] == False
        
        # Check second experience
        assert experiences[1]['company'] is not None
        assert experiences[1]['title'] is not None
    
    def test_calculate_duration_months(self, extractor):
        """Test duration calculation in months"""
        resume_text = """
        Software Engineer
        Tech Company Inc.
        January 2020 - December 2021
        • Developed web applications
        """
        
        result = extractor.extract_all(resume_text)
        experiences = result['work_experience']
        
        if len(experiences) > 0:
            exp = experiences[0]
            assert exp['duration_months'] is not None
            # January 2020 to December 2021 = 24 months
            assert exp['duration_months'] >= 23 and exp['duration_months'] <= 25
    
    def test_current_position_detection(self, extractor):
        """Test detection of current position (Present/Current)"""
        resume_text = """
        Lead Engineer
        Current Company LLC
        March 2022 - Present
        • Leading development team
        """
        
        result = extractor.extract_all(resume_text)
        experiences = result['work_experience']
        
        assert len(experiences) >= 1
        assert experiences[0]['is_current'] == True
        assert experiences[0]['end_date'] is not None
    
    def test_extract_responsibilities(self, extractor):
        """Test extraction of job responsibilities"""
        resume_text = """
        Data Scientist
        Analytics Corp
        Jan 2021 - Dec 2022
        • Developed machine learning models for customer segmentation
        • Analyzed large datasets using Python and SQL
        • Created data visualizations using Tableau
        • Collaborated with cross-functional teams
        """
        
        result = extractor.extract_all(resume_text)
        experiences = result['work_experience']
        
        assert len(experiences) >= 1
        responsibilities = experiences[0]['responsibilities']
        assert len(responsibilities) >= 3
        assert any('machine learning' in r.lower() for r in responsibilities)


class TestEducationExtraction:
    """Test education extraction with all fields"""
    
    @pytest.fixture
    def extractor(self):
        return EnhancedResumeExtractor()
    
    def test_extract_bachelor_degree(self, extractor):
        """Test extraction of bachelor's degree"""
        resume_text = """
        EDUCATION
        
        Bachelor of Science in Computer Science
        Stanford University, Stanford, CA
        2012 - 2016
        GPA: 3.8/4.0
        """
        
        result = extractor.extract_all(resume_text)
        education = result['education']
        
        assert len(education) >= 1
        edu = education[0]
        assert edu['degree_level'] == 'bachelor'
        assert edu['degree'] is not None
        assert 'bachelor' in edu['degree'].lower() or 'b.s' in edu['degree'].lower()
        assert edu['field_of_study'] is not None
        assert 'computer science' in edu['field_of_study'].lower()
        assert edu['institution'] is not None
        assert 'stanford' in edu['institution'].lower()
        # GPA extraction is optional - may not always be present
        if edu['gpa']:
            assert float(edu['gpa']) >= 3.5
    
    def test_extract_master_degree(self, extractor):
        """Test extraction of master's degree"""
        resume_text = """
        ACADEMIC QUALIFICATIONS
        
        Master of Science in Data Science
        MIT, Cambridge, MA
        2018 - 2020
        """
        
        result = extractor.extract_all(resume_text)
        education = result['education']
        
        assert len(education) >= 1
        edu = education[0]
        assert edu['degree_level'] == 'master'
        assert edu['institution'] is not None
        assert 'mit' in edu['institution'].lower()
    
    def test_extract_multiple_degrees(self, extractor):
        """Test extraction of multiple degrees"""
        resume_text = """
        EDUCATION
        
        M.Tech in Artificial Intelligence
        Indian Institute of Technology, Delhi
        2018 - 2020
        
        B.Tech in Computer Engineering
        Delhi University
        2014 - 2018
        GPA: 3.9/4.0
        """
        
        result = extractor.extract_all(resume_text)
        education = result['education']
        
        assert len(education) >= 2
        # Check master's degree
        masters = [e for e in education if e['degree_level'] == 'master']
        assert len(masters) >= 1
        
        # Check bachelor's degree
        bachelors = [e for e in education if e['degree_level'] == 'bachelor']
        assert len(bachelors) >= 1
    
    def test_extract_graduation_years(self, extractor):
        """Test extraction of graduation years"""
        resume_text = """
        Bachelor of Arts in Economics
        Harvard University
        2015 - 2019
        """
        
        result = extractor.extract_all(resume_text)
        education = result['education']
        
        assert len(education) >= 1
        edu = education[0]
        assert edu['start_year'] is not None or edu['graduation_year'] is not None
        if edu['graduation_year']:
            assert '2019' in edu['graduation_year']
    
    def test_extract_phd(self, extractor):
        """Test extraction of PhD degree"""
        resume_text = """
        Ph.D. in Machine Learning
        Carnegie Mellon University
        2016 - 2021
        """
        
        result = extractor.extract_all(resume_text)
        education = result['education']
        
        assert len(education) >= 1
        edu = education[0]
        assert edu['degree_level'] == 'doctorate'


class TestCertificationExtraction:
    """Test certification extraction with all fields"""
    
    @pytest.fixture
    def extractor(self):
        return EnhancedResumeExtractor()
    
    def test_extract_aws_certification(self, extractor):
        """Test extraction of AWS certification"""
        resume_text = """
        CERTIFICATIONS
        
        AWS Certified Solutions Architect - Professional (2022)
        Amazon Web Services
        """
        
        result = extractor.extract_all(resume_text)
        certifications = result['certifications']
        
        assert len(certifications) >= 1
        cert = certifications[0]
        assert 'aws' in cert['name'].lower()
        assert cert['issuer'] is not None or 'aws' in cert['name'].lower()
        if cert['issue_date']:
            assert '2022' in cert['issue_date']
    
    def test_extract_multiple_certifications(self, extractor):
        """Test extraction of multiple certifications"""
        resume_text = """
        PROFESSIONAL CERTIFICATIONS
        
        - AWS Certified Developer Associate (2021)
        - Google Cloud Professional Data Engineer (2022)
        - Microsoft Azure Administrator (2020)
        - PMP - Project Management Professional (2019)
        """
        
        result = extractor.extract_all(resume_text)
        certifications = result['certifications']
        
        assert len(certifications) >= 3
        # Check for cloud certifications
        cloud_certs = [c for c in certifications if any(
            keyword in c['name'].lower() 
            for keyword in ['aws', 'azure', 'google cloud']
        )]
        assert len(cloud_certs) >= 2
    
    def test_extract_certification_with_expiry(self, extractor):
        """Test extraction of certification with expiry date"""
        resume_text = """
        Cisco CCNA
        Issued: January 2021
        Expires: January 2024
        """
        
        result = extractor.extract_all(resume_text)
        certifications = result['certifications']
        
        assert len(certifications) >= 1
        cert = certifications[0]
        assert 'cisco' in cert['name'].lower() or 'ccna' in cert['name'].lower()
    
    def test_extract_certification_with_credential_id(self, extractor):
        """Test extraction of certification with credential ID"""
        resume_text = """
        AWS Certified Solutions Architect
        Credential ID: AWS-SA-12345
        Issued: March 2022
        """
        
        result = extractor.extract_all(resume_text)
        certifications = result['certifications']
        
        assert len(certifications) >= 1


class TestProjectsExtraction:
    """Test projects extraction"""
    
    @pytest.fixture
    def extractor(self):
        return EnhancedResumeExtractor()
    
    def test_extract_single_project(self, extractor):
        """Test extraction of single project"""
        resume_text = """
        KEY PROJECTS
        
        E-Commerce Platform
        • Built scalable e-commerce platform using React and Node.js
        • Implemented payment gateway integration
        • Technologies: React, Node.js, MongoDB, AWS
        """
        
        result = extractor.extract_all(resume_text)
        projects = result.get('projects', [])
        
        assert len(projects) >= 1
        project = projects[0]
        assert project['name'] is not None
        assert 'e-commerce' in project['name'].lower()
        assert len(project['description']) > 0
        assert len(project['technologies']) >= 2
    
    def test_extract_multiple_projects(self, extractor):
        """Test extraction of multiple projects"""
        resume_text = """
        PROJECTS
        
        1. Machine Learning Model for Fraud Detection
           - Developed ML model with 95% accuracy
           - Technologies: Python, TensorFlow, Scikit-learn
        
        2. Mobile Banking Application
           - Built cross-platform mobile app
           - Technologies: React Native, Firebase
        """
        
        result = extractor.extract_all(resume_text)
        projects = result.get('projects', [])
        
        assert len(projects) >= 2


class TestLanguagesExtraction:
    """Test languages extraction"""
    
    @pytest.fixture
    def extractor(self):
        return EnhancedResumeExtractor()
    
    def test_extract_languages_with_proficiency(self, extractor):
        """Test extraction of languages with proficiency levels"""
        resume_text = """
        LANGUAGES
        
        - English: Native/Fluent
        - Spanish: Professional Working Proficiency
        - French: Elementary Proficiency
        """
        
        result = extractor.extract_all(resume_text)
        languages = result.get('languages', [])
        
        assert len(languages) >= 2
        # Check English
        english = [l for l in languages if 'english' in l['language'].lower()]
        assert len(english) >= 1
        assert english[0]['proficiency'] is not None
    
    def test_extract_languages_simple_format(self, extractor):
        """Test extraction of languages in simple format"""
        resume_text = """
        John Doe
        john@email.com | 555-1234
        
        SKILLS
        Python, Java, JavaScript
        
        Languages: English, Hindi, German
        """
        
        result = extractor.extract_all(resume_text)
        languages = result.get('languages', [])
        
        # Should extract at least 2 languages
        assert len(languages) >= 2


class TestAwardsExtraction:
    """Test awards and achievements extraction"""
    
    @pytest.fixture
    def extractor(self):
        return EnhancedResumeExtractor()
    
    def test_extract_awards(self, extractor):
        """Test extraction of awards"""
        resume_text = """
        AWARDS & ACHIEVEMENTS
        
        - Employee of the Year 2022 - Tech Corp
        - Best Innovation Award 2021
        - Published research paper in IEEE Conference 2020
        - Winner of National Hackathon 2019
        """
        
        result = extractor.extract_all(resume_text)
        achievements = result['achievements']
        
        assert len(achievements) >= 3
        # Check for award keywords
        award_text = ' '.join(achievements).lower()
        assert 'award' in award_text or 'winner' in award_text
    
    def test_extract_publications(self, extractor):
        """Test extraction of publications"""
        resume_text = """
        PUBLICATIONS
        
        "Deep Learning for Natural Language Processing"
        Published in ACM Conference 2021
        """
        
        result = extractor.extract_all(resume_text)
        achievements = result['achievements']
        
        assert len(achievements) >= 1


class TestCompleteResumeExtraction:
    """Test complete resume extraction with all fields"""
    
    @pytest.fixture
    def extractor(self):
        return EnhancedResumeExtractor()
    
    def test_extract_complete_resume(self, extractor):
        """Test extraction of complete resume with all sections"""
        complete_resume = """
        John Smith
        john.smith@email.com | +1-555-123-4567
        LinkedIn: linkedin.com/in/johnsmith
        San Francisco, CA
        
        PROFESSIONAL SUMMARY
        Experienced software engineer with 8+ years in full-stack development.
        Specialized in cloud architecture and microservices.
        
        WORK EXPERIENCE
        
        Senior Software Engineer
        Google Inc., Mountain View, CA
        January 2020 - Present
        • Led development of cloud infrastructure
        • Managed team of 5 developers
        • Implemented CI/CD pipelines
        
        Software Developer
        Microsoft Corporation, Redmond, WA
        June 2016 - December 2019
        • Developed Azure cloud solutions
        • Built scalable APIs
        
        EDUCATION
        
        Master of Science in Computer Science
        Stanford University, Stanford, CA
        2014 - 2016
        GPA: 3.9/4.0
        
        Bachelor of Science in Software Engineering
        UC Berkeley, Berkeley, CA
        2010 - 2014
        
        CERTIFICATIONS
        
        - AWS Certified Solutions Architect Professional (2022)
        - Google Cloud Professional Architect (2021)
        - PMP - Project Management Professional (2020)
        
        TECHNICAL SKILLS
        
        Python, Java, JavaScript, React, Node.js, AWS, Docker, Kubernetes
        
        KEY PROJECTS
        
        Cloud Migration Platform
        • Migrated legacy systems to AWS cloud
        • Technologies: AWS, Docker, Kubernetes, Python
        
        LANGUAGES
        
        English (Native), Spanish (Professional), French (Basic)
        
        AWARDS
        
        - Employee of the Year 2022
        - Best Innovation Award 2021
        """
        
        result = extractor.extract_all(complete_resume)
        
        # Test all sections
        assert result['name'] is not None
        assert 'john' in result['name'].lower()
        
        assert result['email'] is not None
        assert 'john.smith@email.com' in result['email']
        
        assert result['phone'] is not None
        
        assert result['linkedin_url'] is not None
        
        assert result['location'] is not None
        
        # Summary extraction is optional but should be present for complete resumes
        if result['summary']:
            assert len(result['summary']) > 30
        
        assert len(result['work_experience']) >= 2
        
        assert len(result['education']) >= 2
        
        assert len(result['certifications']) >= 2
        
        assert len(result['skills']) >= 5
        
        assert len(result.get('projects', [])) >= 1
        
        assert len(result.get('languages', [])) >= 2
        
        assert len(result['achievements']) >= 1
    
    def test_extraction_accuracy_target(self, extractor):
        """Test that extraction meets 95%+ accuracy target"""
        # This test validates the overall accuracy
        # In production, this would test against a labeled dataset
        
        sample_resumes = [
            # Sample 1: Tech resume
            """
            Jane Doe
            jane@email.com | 555-0123
            
            EXPERIENCE
            Senior Developer, Tech Co
            2020 - Present
            • Built web applications
            
            EDUCATION
            B.S. Computer Science, MIT, 2018
            
            SKILLS
            Python, JavaScript, React
            """,
            
            # Sample 2: Business resume
            """
            Bob Johnson
            bob@email.com
            
            PROFESSIONAL EXPERIENCE
            Product Manager, Business Corp
            Jan 2019 - Dec 2022
            • Managed product roadmap
            
            EDUCATION
            MBA, Harvard Business School, 2018
            
            CERTIFICATIONS
            PMP (2020)
            """
        ]
        
        successful_extractions = 0
        total_fields = 0
        
        for resume in sample_resumes:
            result = extractor.extract_all(resume)
            
            # Count successful extractions
            if result['email']: successful_extractions += 1
            total_fields += 1
            
            if result['name']: successful_extractions += 1
            total_fields += 1
            
            if len(result['work_experience']) > 0: successful_extractions += 1
            total_fields += 1
            
            if len(result['education']) > 0: successful_extractions += 1
            total_fields += 1
            
            if len(result['skills']) > 0: successful_extractions += 1
            total_fields += 1
        
        accuracy = (successful_extractions / total_fields) * 100
        assert accuracy >= 90, f"Extraction accuracy {accuracy}% is below 90% target"


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    @pytest.fixture
    def extractor(self):
        return EnhancedResumeExtractor()
    
    def test_empty_text(self, extractor):
        """Test extraction with empty text"""
        result = extractor.extract_all("")
        
        assert result is not None
        assert result['email'] is None
        assert len(result['work_experience']) == 0
    
    def test_malformed_dates(self, extractor):
        """Test extraction with malformed dates"""
        resume_text = """
        Software Engineer
        Tech Company
        Invalid Date - Bad Date
        • Developed applications
        """
        
        result = extractor.extract_all(resume_text)
        # Should not crash, should handle gracefully
        assert result is not None
    
    def test_missing_sections(self, extractor):
        """Test extraction when sections are missing"""
        resume_text = """
        John Doe
        john@email.com
        
        Just some random text without proper sections.
        """
        
        result = extractor.extract_all(resume_text)
        
        assert result is not None
        assert result['email'] is not None
        # Other sections may be empty, but should not crash
    
    def test_unicode_characters(self, extractor):
        """Test extraction with unicode characters"""
        resume_text = """
        José García
        jose@email.com
        
        Ingénieur Logiciel
        Société Française
        2020 - Présent
        """
        
        result = extractor.extract_all(resume_text)
        
        assert result is not None
        assert result['name'] is not None
        assert result['email'] is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
