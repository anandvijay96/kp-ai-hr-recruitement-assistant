#!/usr/bin/env python3
"""Rename app from 'AI Powered HR Assistant' to 'KloudifyHR'"""
import os
import glob

# Find all HTML files
html_files = glob.glob('templates/**/*.html', recursive=True)

replacements = [
    ('AI Powered HR Assistant', 'KloudifyHR'),
    ('AI-Powered HR Assistant', 'KloudifyHR'),
]

count = 0
for filepath in html_files:
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        for old, new in replacements:
            content = content.replace(old, new)
        
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            count += 1
            print(f"✓ Updated: {filepath}")
    except Exception as e:
        print(f"✗ Error processing {filepath}: {e}")

print(f"\n✅ Updated {count} files")
