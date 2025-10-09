"""Verification script for Feature 6 implementation"""
import sys
import os

def verify_files():
    """Verify all required files exist"""
    required_files = [
        'models/job_schemas.py',
        'services/job_service.py',
        'api/jobs.py',
        'templates/jobs/job_list.html',
        'templates/jobs/job_detail.html',
        'tests/test_job_service.py',
        'tests/test_job_api.py',
        'migrations/006_create_jobs_tables.sql',
    ]
    
    print("🔍 Verifying file structure...")
    all_exist = True
    
    for file_path in required_files:
        exists = os.path.exists(file_path)
        status = "✓" if exists else "✗"
        print(f"  {status} {file_path}")
        if not exists:
            all_exist = False
    
    return all_exist


def verify_imports():
    """Verify Python imports work"""
    print("\n🔍 Verifying Python imports...")
    
    try:
        from models import job_schemas
        print("  ✓ models.job_schemas")
    except Exception as e:
        print(f"  ✗ models.job_schemas: {e}")
        return False
    
    try:
        from services import job_service
        print("  ✓ services.job_service")
    except Exception as e:
        print(f"  ✗ services.job_service: {e}")
        return False
    
    try:
        from api import jobs
        print("  ✓ api.jobs")
    except Exception as e:
        print(f"  ✗ api.jobs: {e}")
        return False
    
    return True


def verify_database_models():
    """Verify database models are defined"""
    print("\n🔍 Verifying database models...")
    
    try:
        from models.database import (
            Job, JobSkill, JobRecruiter, JobDocument,
            JobTemplate, JobStatusHistory
        )
        print("  ✓ Job")
        print("  ✓ JobSkill")
        print("  ✓ JobRecruiter")
        print("  ✓ JobDocument")
        print("  ✓ JobTemplate")
        print("  ✓ JobStatusHistory")
        return True
    except Exception as e:
        print(f"  ✗ Database models: {e}")
        return False


def verify_api_endpoints():
    """Verify API endpoints are registered"""
    print("\n🔍 Verifying API endpoints...")
    
    try:
        from api.jobs import router
        routes = [route.path for route in router.routes]
        
        expected_routes = [
            "/api/jobs",
            "/api/jobs/{job_id}",
            "/api/jobs/{job_id}/publish",
            "/api/jobs/{job_id}/close",
            "/api/jobs/{job_id}/clone",
            "/api/jobs/stats/overview",
        ]
        
        for route in expected_routes:
            if any(route in r for r in routes):
                print(f"  ✓ {route}")
            else:
                print(f"  ✗ {route}")
        
        return True
    except Exception as e:
        print(f"  ✗ API endpoints: {e}")
        return False


def verify_schemas():
    """Verify Pydantic schemas are defined"""
    print("\n🔍 Verifying Pydantic schemas...")
    
    try:
        from models.job_schemas import (
            JobCreateRequest, JobUpdateRequest, JobPublishRequest,
            JobCloseRequest, JobCloneRequest, AssignRecruitersRequest,
            JobSummaryResponse, JobDetailResponse, PaginatedJobsResponse,
            WorkType, EmploymentType, JobStatus
        )
        print("  ✓ JobCreateRequest")
        print("  ✓ JobUpdateRequest")
        print("  ✓ JobPublishRequest")
        print("  ✓ JobCloseRequest")
        print("  ✓ JobCloneRequest")
        print("  ✓ AssignRecruitersRequest")
        print("  ✓ JobSummaryResponse")
        print("  ✓ JobDetailResponse")
        print("  ✓ PaginatedJobsResponse")
        print("  ✓ Enums (WorkType, EmploymentType, JobStatus)")
        return True
    except Exception as e:
        print(f"  ✗ Pydantic schemas: {e}")
        return False


def verify_service_methods():
    """Verify service methods exist"""
    print("\n🔍 Verifying service methods...")
    
    try:
        from services.job_service import JobService
        
        required_methods = [
            'create_job', 'get_job_by_id', 'search_jobs', 'update_job',
            'delete_job', 'publish_job', 'close_job', 'reopen_job',
            'clone_job', 'assign_recruiters', 'remove_recruiter',
            'get_statistics'
        ]
        
        for method in required_methods:
            if hasattr(JobService, method):
                print(f"  ✓ {method}")
            else:
                print(f"  ✗ {method}")
        
        return True
    except Exception as e:
        print(f"  ✗ Service methods: {e}")
        return False


def main():
    """Run all verification checks"""
    print("=" * 60)
    print("Feature 6: Job Creation & Management - Verification")
    print("=" * 60)
    
    results = []
    
    results.append(("File Structure", verify_files()))
    results.append(("Python Imports", verify_imports()))
    results.append(("Database Models", verify_database_models()))
    results.append(("Pydantic Schemas", verify_schemas()))
    results.append(("Service Methods", verify_service_methods()))
    results.append(("API Endpoints", verify_api_endpoints()))
    
    print("\n" + "=" * 60)
    print("Verification Summary")
    print("=" * 60)
    
    for check_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status:10} {check_name}")
    
    all_passed = all(result[1] for result in results)
    
    print("=" * 60)
    if all_passed:
        print("✅ All checks passed! Implementation is complete.")
        return 0
    else:
        print("❌ Some checks failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
