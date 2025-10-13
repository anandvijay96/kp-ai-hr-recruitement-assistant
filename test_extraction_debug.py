"""
Debug script to test extraction on actual resume
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from services.enhanced_resume_extractor import EnhancedResumeExtractor
import json

# Sample resume text (based on what we see in the screenshot)
sample_resume = """
Naukri NatikalaShivaShankar

Email: Naukri.Natik@ShivaShankar@gmail.com
Phone: +91-XXXXXXXXXX
LinkedIn: linkedin.com/in/shivashankar-natikala
Location: Pilani, Rajasthan

PROFESSIONAL SUMMARY
Experienced Software Engineer with 7+ years in full-stack development.

SKILLS
AWS, Angular, CSS, Azure, Ag-Grid, Scrum, SQL, HTML, JavaScript, Jquery, C, TypeScript, Agile, Sql Server, Soap, Go, Apache Spark

WORK EXPERIENCE

Software Engineer
Accenture
May 2020 - Nov 2021

Senior Software Engineer  
XYZ Company
Nov 2018 - Apr 2020

Software Developer
ABC Tech
Jan 2016 - Oct 2018

EDUCATION

Bachelor of Engineering
Computer Science
BITS Pilani
2012 - 2016
"""

def main():
    print("=" * 80)
    print("TESTING ENHANCED RESUME EXTRACTOR")
    print("=" * 80)
    
    extractor = EnhancedResumeExtractor()
    
    print("\n1. Testing extraction...")
    result = extractor.extract_all(sample_resume)
    
    print("\n2. EXTRACTION RESULTS:")
    print("-" * 80)
    
    print(f"\nName: {result.get('name')}")
    print(f"Email: {result.get('email')}")
    print(f"Phone: {result.get('phone')}")
    print(f"LinkedIn: {result.get('linkedin_url')}")
    print(f"Location: {result.get('location')}")
    
    print(f"\n\nSkills ({len(result.get('skills', []))}): {result.get('skills')[:10]}")
    
    print(f"\n\nWork Experience ({len(result.get('work_experience', []))}):")
    for i, exp in enumerate(result.get('work_experience', []), 1):
        print(f"\n  Experience {i}:")
        print(f"    Company: {exp.get('company')}")
        print(f"    Title: {exp.get('title')}")
        print(f"    Dates: {exp.get('start_date')} - {exp.get('end_date')}")
        print(f"    Is Current: {exp.get('is_current')}")
        print(f"    Type: {type(exp)}")
    
    print(f"\n\nEducation ({len(result.get('education', []))}):")
    for i, edu in enumerate(result.get('education', []), 1):
        print(f"\n  Education {i}:")
        print(f"    Degree: {edu.get('degree')}")
        print(f"    Field: {edu.get('field_of_study')}")
        print(f"    Institution: {edu.get('institution')}")
        print(f"    Years: {edu.get('start_year')} - {edu.get('graduation_year')}")
        print(f"    Type: {type(edu)}")
    
    print(f"\n\nProjects ({len(result.get('projects', []))}):")
    for i, proj in enumerate(result.get('projects', []), 1):
        print(f"\n  Project {i}:")
        print(f"    Name: {proj.get('name')}")
        print(f"    Technologies: {proj.get('technologies')}")
    
    print(f"\n\nLanguages ({len(result.get('languages', []))}):")
    for i, lang in enumerate(result.get('languages', []), 1):
        print(f"  {i}. {lang.get('language')} - {lang.get('proficiency')}")
    
    print("\n\n3. FULL JSON OUTPUT:")
    print("-" * 80)
    print(json.dumps(result, indent=2, default=str))
    
    print("\n" + "=" * 80)
    print("TESTING COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
