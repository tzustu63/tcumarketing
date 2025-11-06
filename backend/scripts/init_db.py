"""
Database Initialization Script
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.database import engine, Base
from app.models import Task, Contact, ScrapingLog


def init_db():
    """
    Initialize database by creating all tables
    """
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created successfully!")


def drop_db():
    """
    Drop all database tables
    """
    print("Dropping all database tables...")
    Base.metadata.drop_all(bind=engine)
    print("✓ Database tables dropped successfully!")


def reset_db():
    """
    Reset database by dropping and recreating all tables
    """
    print("Resetting database...")
    drop_db()
    init_db()
    print("✓ Database reset completed!")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Database initialization script")
    parser.add_argument(
        "action",
        choices=["init", "drop", "reset"],
        help="Action to perform: init (create tables), drop (drop tables), reset (drop and recreate)"
    )
    
    args = parser.parse_args()
    
    if args.action == "init":
        init_db()
    elif args.action == "drop":
        drop_db()
    elif args.action == "reset":
        reset_db()
