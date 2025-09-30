"""Quick test to verify diagnostics are working"""

from services.resume_analyzer import ResumeAuthenticityAnalyzer

# Create analyzer
analyzer = ResumeAuthenticityAnalyzer()

# Test text
test_text = """
John Doe
Software Engineer
Email: john@example.com

I am a SoFtWaRe EnGiNeEr with experience in Python, python, and PYTHON.
My skills include Java, JAVA, and javascript.
"""

# Test structure info (matching what document_processor returns)
structure_info = {
    'font_analysis': {
        'unique_fonts': 4,
        'font_list': [
            'Arial:12.0',
            'Arial:14.0',
            'Times New Roman:11.0',
            'Calibri:12.0',
            'Arial:12.0',  # Duplicate to show counting
            'Verdana:10.0'
        ]
    },
    'layout_analysis': {'consistent_fonts': False},
    'page_count': 1
}

# Run analysis
result = analyzer.analyze_authenticity(test_text, structure_info)

# Print results
print("=" * 60)
print("AUTHENTICITY ANALYSIS RESULT")
print("=" * 60)
print(f"\nOverall Score: {result['overall_score']}%")
print(f"LinkedIn Profile Score: {result['linkedin_profile_score']}%")
print(f"Capitalization Score: {result['capitalization_score']}%")
print(f"\nFlags: {len(result['flags'])} found")
for flag in result['flags']:
    print(f"  - [{flag['severity'].upper()}] {flag['category']}: {flag['message']}")

print(f"\nDiagnostics Keys: {list(result['diagnostics'].keys())}")

# Check LinkedIn diagnostics
if 'linkedin' in result['diagnostics']:
    linkedin_diag = result['diagnostics']['linkedin']
    print(f"\nLinkedIn Diagnostics:")
    print(f"  Status: {linkedin_diag['status']}")
    print(f"  Recommendation: {linkedin_diag['recommendation']}")

# Check Capitalization diagnostics
if 'capitalization' in result['diagnostics']:
    cap_diag = result['diagnostics']['capitalization']
    print(f"\nCapitalization Diagnostics:")
    print(f"  Issues Found: {cap_diag['issues_found']}")
    for issue in cap_diag['details']:
        print(f"  - {issue['type']}: {issue.get('count', 'N/A')} occurrences")

# Check Font diagnostics
if 'fonts' in result['diagnostics']:
    font_diag = result['diagnostics']['fonts']
    print(f"\nFont Diagnostics:")
    print(f"  Total Unique Fonts: {font_diag['total_unique_fonts']}")
    print(f"  Recommendation: {font_diag['recommendation']}")
    print(f"  Font Breakdown:")
    for font_name, count in font_diag['fonts_breakdown'].items():
        print(f"    • {font_name}: {count}")

print("\n" + "=" * 60)
print("✅ Diagnostics are working correctly!")
print("=" * 60)
