text = """    
Pulavarthy Pranathi    
Salesforce Marketing Cloud Developer    
E-mail
  
Contact No: +91 8790266153    
LinkedIn: https://www.linkedin.com/in/pranathi-pulavarthy-029445150    
"""

lines = text.strip().split('\n')[:10]
print("Lines:")
for i, line in enumerate(lines):
    line = line.strip()
    print(f"{i}: '{line}' (len={len(line)})")
    
    if len(line) > 5 and len(line) < 50:
        words = line.split()
        print(f"   Words: {words}")
        print(f"   All uppercase first?: {all(w[0].isupper() for w in words if w)}")
        
        if 2 <= len(words) <= 4 and all(w[0].isupper() for w in words if w):
            if not any(keyword in line.lower() for keyword in ['email', 'phone', 'contact', 'linkedin', 'resume', 'cv', 'developer', 'engineer', 'manager']):
                print(f"   ✅ MATCH: {line}")
                break
            else:
                print(f"   ❌ Contains keyword")
