"""
Comprehensive route verification script
Checks that all features have both API routes and web routes
"""

import os
import re

def check_routes():
    """Check all routes in main.py"""
    
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("\n" + "="*70)
    print("ROUTE VERIFICATION REPORT")
    print("="*70 + "\n")
    
    # Extract all web routes
    web_routes = re.findall(r'@app\.get\("(/[^"]+)"\)', content)
    
    print("📄 WEB ROUTES (HTML Pages):")
    print("-" * 70)
    
    features = {
        'Dashboard': ['/'],
        'Authentication': ['/login', '/register'],
        'Candidates': ['/candidates', '/candidates/create', '/candidates/{candidate_id}', '/candidates/{candidate_id}/edit'],
        'Jobs': ['/jobs', '/jobs/create', '/jobs/{job_id}', '/jobs/{job_id}/edit'],
        'Jobs Management': ['/jobs-management/dashboard', '/jobs-management/{job_id}/analytics', '/jobs-management/{job_id}/audit-log'],
        'Users': ['/users', '/users/{user_id}'],
        'Clients': ['/clients', '/clients/create', '/clients/{client_id}', '/clients/{client_id}/edit'],
        'Vendors': ['/vendors', '/vendors/create', '/vendors/{vendor_id}', '/vendors/{vendor_id}/edit']
    }
    
    all_good = True
    
    for feature, expected_routes in features.items():
        print(f"\n{feature}:")
        for route in expected_routes:
            # Check if route exists (handle path parameters)
            route_pattern = route.replace('{', '\\{').replace('}', '\\}')
            if any(re.match(route_pattern.replace('\\{[^}]+\\}', '[^/]+'), r) for r in web_routes):
                print(f"  ✅ {route}")
            else:
                print(f"  ❌ {route} - MISSING!")
                all_good = False
    
    # Check templates directory
    print("\n\n📁 TEMPLATE FILES:")
    print("-" * 70)
    
    template_dirs = {
        'auth': ['login.html', 'register.html'],
        'candidates': ['list.html', 'create.html', 'detail.html', 'edit.html'],
        'jobs': ['job_list.html', 'job_create.html', 'job_detail.html', 'job_edit.html'],
        'jobs_management': ['dashboard.html', 'analytics.html', 'audit_log.html'],
        'users': ['list.html', 'detail.html'],
        'clients': ['list.html', 'create.html', 'detail.html', 'edit.html'],
        'vendors': ['list.html', 'create.html', 'detail.html', 'edit.html']
    }
    
    for dir_name, files in template_dirs.items():
        dir_path = f'templates/{dir_name}'
        print(f"\n{dir_name}:")
        if os.path.exists(dir_path):
            existing_files = os.listdir(dir_path)
            for file in files:
                if file in existing_files:
                    print(f"  ✅ {file}")
                else:
                    print(f"  ❌ {file} - MISSING!")
                    all_good = False
        else:
            print(f"  ❌ Directory not found!")
            all_good = False
    
    # Check API routers
    print("\n\n🔌 API ROUTERS:")
    print("-" * 70)
    
    api_files = [
        'auth.py', 'resumes.py', 'candidates.py', 'jobs.py', 
        'jobs_management.py', 'users.py', 'clients.py', 'vendors.py'
    ]
    
    for api_file in api_files:
        api_path = f'api/{api_file}'
        if os.path.exists(api_path):
            print(f"  ✅ {api_file}")
        else:
            print(f"  ❌ {api_file} - MISSING!")
            all_good = False
    
    # Check router registration in main.py
    print("\n\n📋 ROUTER REGISTRATION IN main.py:")
    print("-" * 70)
    
    expected_imports = [
        'auth', 'resumes', 'candidates', 'jobs', 
        'jobs_management', 'users', 'clients', 'vendors'
    ]
    
    import_line = re.search(r'from api import (.+)', content)
    if import_line:
        imported = [x.strip() for x in import_line.group(1).split(',')]
        for module in expected_imports:
            if module in imported:
                print(f"  ✅ {module}")
            else:
                print(f"  ❌ {module} - NOT IMPORTED!")
                all_good = False
    
    # Check include_router calls
    router_includes = re.findall(r'app\.include_router\((\w+)\.router\)', content)
    print("\n  Router Includes:")
    for module in expected_imports:
        if module in router_includes:
            print(f"    ✅ {module}.router")
        else:
            print(f"    ❌ {module}.router - NOT INCLUDED!")
            all_good = False
    
    # Summary
    print("\n\n" + "="*70)
    if all_good:
        print("✅ ALL CHECKS PASSED!")
        print("="*70)
        print("\n🎉 All features have proper routes and templates!")
        print("\nYou can now access:")
        print("  • Vendors: http://localhost:8000/vendors")
        print("  • Clients: http://localhost:8000/clients")
        print("  • Jobs: http://localhost:8000/jobs")
        print("  • Users: http://localhost:8000/users")
        print("  • Candidates: http://localhost:8000/candidates")
        print("\n⚠️  IMPORTANT: Restart your server for changes to take effect!")
        print("   Command: uvicorn main:app --reload")
    else:
        print("❌ SOME CHECKS FAILED!")
        print("="*70)
        print("\n⚠️  Please fix the missing items above.")
    print()

if __name__ == "__main__":
    try:
        check_routes()
    except Exception as e:
        print(f"\n❌ Error running verification: {e}")
        import traceback
        traceback.print_exc()
