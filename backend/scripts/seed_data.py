"""
Seed Data Script - Create sample data for testing
"""
import sys
import os
from datetime import datetime
import uuid

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.database import SessionLocal
from app.models import Task, Contact, ScrapingLog


def seed_tasks():
    """Create sample tasks"""
    db = SessionLocal()
    
    try:
        tasks = [
            {
                "id": uuid.uuid4(),
                "keyword": "SMA Internasional",
                "city": "Jakarta",
                "target_platforms": ["website", "facebook"],
                "max_results": 50,
                "status": "completed",
                "progress": 100,
                "results_count": 15,
                "created_at": datetime.utcnow(),
                "completed_at": datetime.utcnow(),
            },
            {
                "id": uuid.uuid4(),
                "keyword": "Pusat Bahasa Mandarin",
                "city": "Surabaya",
                "target_platforms": ["website", "instagram"],
                "max_results": 30,
                "status": "running",
                "progress": 60,
                "results_count": 8,
                "created_at": datetime.utcnow(),
                "started_at": datetime.utcnow(),
            },
            {
                "id": uuid.uuid4(),
                "keyword": "Agen Pendidikan",
                "city": "Bandung",
                "target_platforms": ["website"],
                "max_results": 20,
                "status": "pending",
                "progress": 0,
                "results_count": 0,
                "created_at": datetime.utcnow(),
            },
        ]
        
        for task_data in tasks:
            task = Task(**task_data)
            db.add(task)
        
        db.commit()
        print(f"✓ Created {len(tasks)} sample tasks")
        return [task["id"] for task in tasks]
        
    except Exception as e:
        print(f"✗ Error creating tasks: {e}")
        db.rollback()
        return []
    finally:
        db.close()


def seed_contacts(task_ids):
    """Create sample contacts"""
    if not task_ids:
        print("✗ No task IDs provided, skipping contacts")
        return
    
    db = SessionLocal()
    
    try:
        contacts = [
            {
                "task_id": task_ids[0],
                "institution_name": "SMA Global Mandiri Jakarta",
                "institution_type": "高中",
                "source_url": "https://example.com/sma-global",
                "source_platform": "website",
                "email": "info@smaglobal.sch.id",
                "whatsapp": "+628123456789",
                "quality_score": 90.0,
                "extracted_at": datetime.utcnow(),
            },
            {
                "task_id": task_ids[0],
                "institution_name": "International School Jakarta",
                "institution_type": "高中",
                "source_url": "https://example.com/isj",
                "source_platform": "facebook",
                "email": "admission@isj.ac.id",
                "whatsapp": "+628234567890",
                "quality_score": 85.0,
                "extracted_at": datetime.utcnow(),
            },
            {
                "task_id": task_ids[1],
                "institution_name": "Pusat Bahasa Mandarin Surabaya",
                "institution_type": "華語中心",
                "source_url": "https://example.com/pbm-sby",
                "source_platform": "website",
                "email": "contact@pbmsurabaya.co.id",
                "quality_score": 75.0,
                "extracted_at": datetime.utcnow(),
            },
        ]
        
        for contact_data in contacts:
            contact = Contact(**contact_data)
            db.add(contact)
        
        db.commit()
        print(f"✓ Created {len(contacts)} sample contacts")
        
    except Exception as e:
        print(f"✗ Error creating contacts: {e}")
        db.rollback()
    finally:
        db.close()


def seed_logs(task_ids):
    """Create sample scraping logs"""
    if not task_ids:
        print("✗ No task IDs provided, skipping logs")
        return
    
    db = SessionLocal()
    
    try:
        logs = [
            {
                "task_id": task_ids[0],
                "url": "https://www.google.com/search?q=SMA+Internasional+Jakarta",
                "action": "google_search",
                "status": "success",
                "response_time": 1250,
                "created_at": datetime.utcnow(),
            },
            {
                "task_id": task_ids[0],
                "url": "https://example.com/sma-global",
                "action": "extract_website",
                "status": "success",
                "response_time": 2100,
                "created_at": datetime.utcnow(),
            },
            {
                "task_id": task_ids[1],
                "url": "https://example.com/pbm-sby",
                "action": "extract_website",
                "status": "error",
                "error_message": "Connection timeout",
                "response_time": 5000,
                "created_at": datetime.utcnow(),
            },
        ]
        
        for log_data in logs:
            log = ScrapingLog(**log_data)
            db.add(log)
        
        db.commit()
        print(f"✓ Created {len(logs)} sample logs")
        
    except Exception as e:
        print(f"✗ Error creating logs: {e}")
        db.rollback()
    finally:
        db.close()


def seed_all():
    """Seed all sample data"""
    print("Seeding database with sample data...")
    task_ids = seed_tasks()
    seed_contacts(task_ids)
    seed_logs(task_ids)
    print("✓ Database seeding completed!")


def clear_all():
    """Clear all data from database"""
    db = SessionLocal()
    
    try:
        print("Clearing all data...")
        db.query(ScrapingLog).delete()
        db.query(Contact).delete()
        db.query(Task).delete()
        db.commit()
        print("✓ All data cleared!")
        
    except Exception as e:
        print(f"✗ Error clearing data: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Database seeding script")
    parser.add_argument(
        "action",
        choices=["seed", "clear"],
        help="Action to perform: seed (create sample data), clear (delete all data)"
    )
    
    args = parser.parse_args()
    
    if args.action == "seed":
        seed_all()
    elif args.action == "clear":
        clear_all()
