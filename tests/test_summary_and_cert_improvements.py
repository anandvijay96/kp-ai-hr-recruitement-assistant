"""
Additional Test Cases for Phase 1 Improvements
Tests for enhanced professional summary and certifications extraction
"""

import pytest
from services.enhanced_resume_extractor import EnhancedResumeExtractor


class TestProfessionalSummaryEnhancements:
    """Test enhanced professional summary extraction"""
    
    @pytest.fixture
    def extractor(self):
        return EnhancedResumeExtractor()
    
    def test_summary_with_explicit_header(self, extractor):
        """Test extraction when summary has explicit header"""
        resume_text = """
        John Doe
        john@email.com
        
        PROFESSIONAL SUMMARY
        Experienced software engineer with 10+ years in full-stack development.
        Proven track record of delivering scalable solutions.
        
        EXPERIENCE
        Senior Developer, Tech Corp
        2020 - Present
        """
        
        result = extractor.extract_all(resume_text)
        summary = result['summary']
        
        assert summary is not None
        assert len(summary) >= 20
        assert 'experienced' in summary.lower() or 'software' in summary.lower()
        assert 'experience' not in summary.lower() or 'senior developer' not in summary.lower()
    
    def test_summary_with_profile_header(self, extractor):
        """Test extraction when using 'Profile' header"""
        resume_text = """
        Jane Smith
        jane@email.com
        
        PROFILE
        Data scientist passionate about machine learning and AI.
        Skilled in Python, TensorFlow, and big data analytics.
        
        WORK EXPERIENCE
        ML Engineer, AI Company
        """
        
        result = extractor.extract_all(resume_text)
        summary = result['summary']
        
        assert summary is not None
        assert 'data scientist' in summary.lower() or 'machine learning' in summary.lower()
    
    def test_summary_with_objective_header(self, extractor):
        """Test extraction when using 'Objective' header"""
        resume_text = """
        Bob Johnson
        bob@email.com
        
        OBJECTIVE:
        Seeking a challenging role in software development to utilize
        my skills in Java and cloud technologies.
        
        SKILLS
        Java, AWS, Docker
        """
        
        result = extractor.extract_all(resume_text)
        summary = result['summary']
        
        assert summary is not None
        assert 'seeking' in summary.lower() or 'software development' in summary.lower()
    
    def test_summary_fallback_top_paragraph(self, extractor):
        """Test fallback extraction of paragraph at top of resume"""
        resume_text = """
        Alice Brown
        alice@email.com | 555-1234
        
        Results-driven project manager with 7 years of experience leading
        cross-functional teams. Expert in Agile methodologies and stakeholder management.
        
        EXPERIENCE
        Project Manager, Tech Solutions
        2018 - Present
        """
        
        result = extractor.extract_all(resume_text)
        summary = result['summary']
        
        # Should extract the paragraph even without explicit header
        assert summary is not None
        assert 'project manager' in summary.lower()
        assert len(summary) >= 20
    
    def test_summary_skips_contact_info(self, extractor):
        """Test that summary doesn't include contact information"""
        resume_text = """
        Charlie Wilson
        charlie@email.com
        linkedin.com/in/charlie
        +1-555-9876
        
        SUMMARY
        Full-stack developer with expertise in React and Node.js.
        Passionate about building user-friendly applications.
        
        EXPERIENCE
        Developer, Web Co
        """
        
        result = extractor.extract_all(resume_text)
        summary = result['summary']
        
        assert summary is not None
        assert '@' not in summary  # No email
        assert 'linkedin.com' not in summary.lower()  # No LinkedIn URL
        assert not any(char.isdigit() for c in summary if c.startswith('+'))  # No phone
    
    def test_summary_stops_at_section_header(self, extractor):
        """Test that summary extraction stops at next section"""
        resume_text = """
        Emma Davis
        emma@email.com
        
        PROFESSIONAL OVERVIEW
        Senior analyst with strong background in data visualization.
        
        EXPERIENCE
        Data Analyst, Analytics Inc
        """
        
        result = extractor.extract_all(resume_text)
        summary = result['summary']
        
        assert summary is not None
        assert 'analyst' in summary.lower()
        assert 'analytics inc' not in summary.lower()  # Should not include experience section
    
    def test_summary_length_validation(self, extractor):
        """Test that summary has reasonable length"""
        resume_text = """
        Test Person
        test@email.com
        
        SUMMARY
        Expert developer with extensive experience in multiple programming
        languages and frameworks. Proven ability to deliver high-quality
        software solutions on time and within budget. Strong communication
        skills and team leadership experience.
        
        SKILLS
        Python, Java
        """
        
        result = extractor.extract_all(resume_text)
        summary = result['summary']
        
        assert summary is not None
        assert 20 <= len(summary) <= 1500  # Reasonable length


class TestCertificationEnhancements:
    """Test enhanced certification extraction with better validation"""
    
    @pytest.fixture
    def extractor(self):
        return EnhancedResumeExtractor()
    
    def test_cert_with_year_in_parentheses(self, extractor):
        """Test certification with year in parentheses"""
        resume_text = """
        CERTIFICATIONS
        
        - AWS Certified Solutions Architect (2022)
        - Azure Administrator Associate (2021)
        """
        
        result = extractor.extract_all(resume_text)
        certs = result['certifications']
        
        assert len(certs) >= 2
        aws_cert = [c for c in certs if 'aws' in c['name'].lower()][0]
        assert '2022' in (aws_cert['issue_date'] or '')
    
    def test_cert_excludes_work_experience(self, extractor):
        """Test that work experience is not mistaken for certifications"""
        resume_text = """
        CERTIFICATIONS
        
        - PMP Certified (2020)
        
        Lead Engineer at Tech Corp 2018-2020
        """
        
        result = extractor.extract_all(resume_text)
        certs = result['certifications']
        
        # Should have PMP but not the work experience
        assert len(certs) >= 1
        assert any('pmp' in c['name'].lower() for c in certs)
        assert not any('lead engineer' in c['name'].lower() for c in certs)
    
    def test_cert_well_known_abbreviations(self, extractor):
        """Test extraction of well-known certification abbreviations"""
        resume_text = """
        CERTIFICATIONS
        
        - CPA
        - CFA Level II
        - CISSP
        - CCNA
        """
        
        result = extractor.extract_all(resume_text)
        certs = result['certifications']
        
        # Should recognize these well-known certs
        assert len(certs) >= 3
        cert_names = ' '.join([c['name'].lower() for c in certs])
        assert 'cpa' in cert_names or 'cfa' in cert_names or 'cissp' in cert_names
    
    def test_cert_excludes_file_paths(self, extractor):
        """Test that file paths are not extracted as certifications"""
        resume_text = """
        CERTIFICATIONS
        
        - AWS Certified Developer (2021)
        file:///C:/Users/Documents/cert.pdf
        """
        
        result = extractor.extract_all(resume_text)
        certs = result['certifications']
        
        # Should have AWS cert but not the file path
        assert len(certs) >= 1
        assert not any('file:///' in c['name'].lower() for c in certs)
    
    def test_cert_with_certification_keyword(self, extractor):
        """Test certification names containing 'certified' keyword"""
        resume_text = """
        PROFESSIONAL CERTIFICATIONS
        
        Certified Kubernetes Administrator
        Certified Ethical Hacker
        Microsoft Certified: Azure Developer Associate
        """
        
        result = extractor.extract_all(resume_text)
        certs = result['certifications']
        
        assert len(certs) >= 2
        # All should contain certification-related keywords
        for cert in certs:
            assert any(keyword in cert['name'].lower() 
                      for keyword in ['certified', 'administrator', 'hacker', 'developer', 'associate'])
    
    def test_cert_excludes_job_titles(self, extractor):
        """Test that job titles are not extracted as certifications"""
        resume_text = """
        CERTIFICATIONS
        
        - AWS Solutions Architect Certification (2022)
        
        Senior Developer at Company Inc
        Project Manager at Business Corp
        """
        
        result = extractor.extract_all(resume_text)
        certs = result['certifications']
        
        # Should have AWS cert but not the job titles
        assert len(certs) >= 1
        assert any('aws' in c['name'].lower() for c in certs)
        assert not any('at company' in c['name'].lower() for c in certs)
        assert not any('at business' in c['name'].lower() for c in certs)
    
    def test_cert_deduplication(self, extractor):
        """Test that duplicate certifications are removed"""
        resume_text = """
        CERTIFICATIONS
        
        - AWS Certified Solutions Architect (2022)
        - AWS Certified Solutions Architect (2022)
        - Azure Administrator (2021)
        """
        
        result = extractor.extract_all(resume_text)
        certs = result['certifications']
        
        # Should have 2 unique certs, not 3
        assert len(certs) == 2
        cert_names = [c['name'].lower() for c in certs]
        assert len(cert_names) == len(set(cert_names))  # No duplicates
    
    def test_cert_reasonable_length(self, extractor):
        """Test that certification names have reasonable length"""
        resume_text = """
        CERTIFICATIONS
        
        AB
        AWS Certified Solutions Architect Professional
        This is a very very very very very very long certification name that goes on and on and on for way too many characters and should probably be filtered out because it's unreasonably long
        """
        
        result = extractor.extract_all(resume_text)
        certs = result['certifications']
        
        # Should exclude very short and very long names
        for cert in certs:
            assert 5 <= len(cert['name']) <= 200


class TestIntegrationImprovements:
    """Test integration of all improvements"""
    
    @pytest.fixture
    def extractor(self):
        return EnhancedResumeExtractor()
    
    def test_complete_resume_with_improvements(self, extractor):
        """Test complete resume extraction with all improvements"""
        resume_text = """
        Sarah Johnson
        sarah.johnson@email.com | +1-555-2468
        San Francisco, CA
        
        Results-oriented software architect with 12+ years of experience designing
        and implementing large-scale distributed systems. Expert in cloud architecture,
        microservices, and DevOps practices.
        
        PROFESSIONAL EXPERIENCE
        
        Principal Software Architect
        Tech Giants Inc., San Francisco, CA
        March 2020 - Present
        • Lead architecture design for cloud-native applications
        • Mentor team of 10 senior engineers
        • Reduced system latency by 60% through optimization
        
        Senior Software Engineer
        Innovation Labs, Palo Alto, CA
        June 2015 - February 2020
        • Designed microservices architecture
        • Implemented CI/CD pipelines
        
        EDUCATION
        
        Master of Science in Computer Science
        Stanford University, 2015
        
        Bachelor of Engineering in Software Engineering
        UC Berkeley, 2013
        
        CERTIFICATIONS
        
        - AWS Certified Solutions Architect Professional (2023)
        - Google Cloud Professional Architect (2022)
        - TOGAF 9 Certified (2021)
        - Certified Kubernetes Administrator (2020)
        
        TECHNICAL SKILLS
        
        Python, Java, Golang, React, Node.js, AWS, GCP, Kubernetes, Docker,
        Terraform, PostgreSQL, MongoDB, Redis
        """
        
        result = extractor.extract_all(resume_text)
        
        # Test name and contact
        assert result['name'] is not None
        assert 'sarah' in result['name'].lower()
        assert result['email'] == 'sarah.johnson@email.com'
        assert result['phone'] is not None
        
        # Test improved summary extraction
        assert result['summary'] is not None
        assert len(result['summary']) >= 50
        assert 'software architect' in result['summary'].lower()
        assert 'years of experience' in result['summary'].lower()
        # Should not contain work experience section
        assert 'tech giants' not in result['summary'].lower()
        
        # Test work experience
        assert len(result['work_experience']) >= 2
        principal_role = [exp for exp in result['work_experience'] 
                         if 'principal' in exp['title'].lower() or 'architect' in exp['title'].lower()]
        assert len(principal_role) >= 1
        
        # Test education
        assert len(result['education']) >= 2
        
        # Test improved certifications (should have 4, all valid)
        assert len(result['certifications']) >= 4
        cert_names = [c['name'].lower() for c in result['certifications']]
        assert any('aws' in name for name in cert_names)
        assert any('google' in name or 'gcp' in name for name in cert_names)
        assert any('kubernetes' in name for name in cert_names)
        
        # No work experience should be in certifications
        assert not any('tech giants' in c['name'].lower() for c in result['certifications'])
        assert not any('innovation labs' in c['name'].lower() for c in result['certifications'])
        
        # Test skills
        assert len(result['skills']) >= 10
        assert 'Python' in result['skills'] or 'python' in [s.lower() for s in result['skills']]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
