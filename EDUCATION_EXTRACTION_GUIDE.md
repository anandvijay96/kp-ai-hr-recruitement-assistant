# Education Extraction Troubleshooting Guide

## Issue
Education information is not being extracted from some resumes.

## Common Causes

### 1. **Missing Education Section Header**
The parser looks for keywords like:
- Education
- Academic Qualifications
- Educational Background
- Degree
- University
- College

**Solution:** Ensure resumes have a clear section header.

### 2. **Unrecognized Degree Format**
The parser recognizes:
- B.Tech, M.Tech, B.E., M.E.
- B.Sc, M.Sc, BSc, MSc
- MBA, BBA, MCA, BCA
- Bachelor of..., Master of...
- PhD, Doctorate
- Diploma

**Solution:** Add more degree patterns if needed.

### 3. **Text Extraction Failed**
If the PDF is scanned or image-based, text extraction might fail.

**Solution:** Use OCR-enabled PDF processing.

## Debugging Steps

### Step 1: Check if Text Was Extracted
1. Go to the resume detail page in the admin panel
2. Check if `extracted_text` field has content
3. If empty, the PDF/DOCX parsing failed

### Step 2: Manual Test
Run this in Python console:

```python
from services.resume_parser_service import ResumeParserService
import asyncio

# Read your resume file
with open('path/to/resume.pdf', 'rb') as f:
    content = f.read()

# Parse it
parser = ResumeParserService()
result = asyncio.run(parser.parse_resume_structured(content, 'pdf'))

# Check education
print("Education found:", result.get('education'))
```

### Step 3: Check Resume Format
Open the resume and verify:
- [ ] Has clear "Education" section
- [ ] Degree names are standard (B.Tech, M.Sc, etc.)
- [ ] University/College names are present
- [ ] Years are in format: 2020-2024 or 2020

## Improving Extraction

### Option 1: Add More Patterns
Edit `services/resume_parser_service.py` and add more degree patterns:

```python
degree_patterns = [
    r'\b(Your Custom Pattern)\b',
    # ... existing patterns
]
```

### Option 2: Use AI-Based Parsing
Integrate OpenAI or Google Gemini for better extraction:

```python
# Example with OpenAI
import openai

def extract_education_with_ai(text):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{
            "role": "user",
            "content": f"Extract education details from this resume:\n{text}"
        }]
    )
    return response.choices[0].message.content
```

### Option 3: Manual Entry
If parsing fails, users can manually add education via the edit page.

## Testing Different Resume Formats

### Test Case 1: Standard Format
```
EDUCATION
B.Tech in Computer Science
ABC University, 2020-2024
CGPA: 8.5/10
```

### Test Case 2: Abbreviated Format
```
Education
BTech CSE | XYZ College | 2020-24
```

### Test Case 3: Full Names
```
ACADEMIC QUALIFICATIONS
Bachelor of Technology in Information Technology
University of Example, 2020-2024
```

### Test Case 4: Multiple Degrees
```
EDUCATION
Master of Science in Data Science
Stanford University, 2022-2024

Bachelor of Engineering in Computer Science
MIT, 2018-2022
```

## Expected Output

The parser should extract:
```json
{
  "education": [
    {
      "degree": "B.Tech Computer Science",
      "institution": "ABC University",
      "start_date": "2020",
      "end_date": "2024",
      "gpa": "8.5",
      "field": "Computer Science",
      "location": null,
      "confidence": 0.9
    }
  ]
}
```

## Fallback Strategy

If automated extraction fails:
1. Resume is still uploaded and stored
2. Candidate record is created with available info
3. User can manually edit and add education
4. Or re-upload a better formatted resume

## Recommended Resume Format

For best extraction results, advise candidates to format resumes as:

```
EDUCATION

Bachelor of Technology in Computer Science Engineering
ABC University, City, State
2020 - 2024
CGPA: 8.5/10.0

Higher Secondary (12th)
XYZ School, City
2019 - 2020
Percentage: 85%
```

## Future Improvements

1. **AI Integration**: Use LLMs for better extraction
2. **OCR Support**: Handle scanned PDFs
3. **Manual Review**: Flag low-confidence extractions
4. **Template Matching**: Recognize common resume templates
5. **User Feedback**: Learn from corrections

## Support

If education extraction continues to fail:
1. Check the resume file format
2. Verify text extraction worked
3. Review server logs for errors
4. Consider manual entry as fallback
5. Report issue with sample resume for improvement
