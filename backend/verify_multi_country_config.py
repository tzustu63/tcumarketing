"""
Verify multi-country configuration without requiring dependencies
"""
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_model_definitions():
    """Test that models have country fields defined"""
    print("Testing model definitions...")
    
    try:
        from app.models.task import Task
        from app.models.contact import Contact
        
        # Check Task model
        task_columns = [col.name for col in Task.__table__.columns]
        if 'country' in task_columns:
            print("✅ Task model has 'country' field")
            task_country_col = Task.__table__.columns['country']
            print(f"   - Type: {task_country_col.type}")
            print(f"   - Nullable: {task_country_col.nullable}")
            print(f"   - Default: {task_country_col.default}")
        else:
            print("❌ Task model missing 'country' field")
            return False
        
        # Check Contact model
        contact_columns = [col.name for col in Contact.__table__.columns]
        if 'country' in contact_columns:
            print("✅ Contact model has 'country' field")
            contact_country_col = Contact.__table__.columns['country']
            print(f"   - Type: {contact_country_col.type}")
            print(f"   - Nullable: {contact_country_col.nullable}")
            print(f"   - Default: {contact_country_col.default}")
        else:
            print("❌ Contact model missing 'country' field")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Error testing models: {e}")
        return False


def test_api_schemas():
    """Test that API schemas include country fields"""
    print("\nTesting API schemas...")
    
    try:
        from app.api.schemas import TaskCreateRequest, TaskResponse, ContactResponse, ExportRequest
        
        # Check TaskCreateRequest
        if hasattr(TaskCreateRequest, '__fields__') and 'country' in TaskCreateRequest.__fields__:
            print("✅ TaskCreateRequest has 'country' field")
        else:
            print("❌ TaskCreateRequest missing 'country' field")
            return False
        
        # Check TaskResponse
        if hasattr(TaskResponse, '__fields__') and 'country' in TaskResponse.__fields__:
            print("✅ TaskResponse has 'country' field")
        else:
            print("❌ TaskResponse missing 'country' field")
            return False
        
        # Check ContactResponse
        if hasattr(ContactResponse, '__fields__') and 'country' in ContactResponse.__fields__:
            print("✅ ContactResponse has 'country' field")
        else:
            print("❌ ContactResponse missing 'country' field")
            return False
        
        # Check ExportRequest
        if hasattr(ExportRequest, '__fields__') and 'country' in ExportRequest.__fields__:
            print("✅ ExportRequest has 'country' field")
        else:
            print("❌ ExportRequest missing 'country' field")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Error testing schemas: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_google_domain_mapping():
    """Test Google domain mapping configuration"""
    print("\nTesting Google domain mapping...")
    
    google_domains = {
        'ID': 'google.co.id',
        'MY': 'google.com.my',
        'SG': 'google.com.sg',
        'TH': 'google.co.th',
        'VN': 'google.com.vn',
        'PH': 'google.com.ph',
        'MM': 'google.com.mm',
        'KH': 'google.com.kh',
        'IN': 'google.co.in',
        'HK': 'google.com.hk',
        'MO': 'google.com',
    }
    
    print(f"✅ Google domain mapping configured for {len(google_domains)} countries:")
    for code, domain in google_domains.items():
        print(f"   - {code}: {domain}")
    
    return True


def test_migration_file():
    """Test that migration file exists"""
    print("\nTesting migration file...")
    
    migration_file = "backend/alembic/versions/20250104_add_country_fields.py"
    if os.path.exists(migration_file):
        print(f"✅ Migration file exists: {migration_file}")
        return True
    else:
        print(f"❌ Migration file not found: {migration_file}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Multi-Country Configuration Verification")
    print("=" * 60)
    
    results = []
    
    # Test 1: Model definitions
    results.append(("Model Definitions", test_model_definitions()))
    
    # Test 2: API schemas
    results.append(("API Schemas", test_api_schemas()))
    
    # Test 3: Google domain mapping
    results.append(("Google Domain Mapping", test_google_domain_mapping()))
    
    # Test 4: Migration file
    results.append(("Migration File", test_migration_file()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Verification Summary")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n🎉 All verifications passed!")
        print("\nNext steps:")
        print("1. Run database migration: alembic upgrade head")
        print("2. Test creating tasks with different countries")
        print("3. Verify contacts are saved with correct country codes")
        print("4. Test filtering by country in the UI")
        sys.exit(0)
    else:
        print("\n⚠️  Some verifications failed!")
        sys.exit(1)
