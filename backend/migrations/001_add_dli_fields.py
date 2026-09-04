"""
Migration: Add DLI fields to predictions table

This migration adds nullable DLI (Deep Learning Index) fields to the predictions table
to support detailed document analysis while maintaining backward compatibility with
existing simple classification predictions.

Usage:
    python backend/migrations/001_add_dli_fields.py

Requirements:
    - SQLite database at ./educlassify.db
    - Backup database before running migration
"""

import sqlite3
import os
import sys
from datetime import datetime


def backup_database(db_path: str) -> str:
    """Create a backup of the database before migration"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{db_path}.backup_{timestamp}"
    
    if os.path.exists(db_path):
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"✓ Database backed up to: {backup_path}")
        return backup_path
    else:
        print(f"⚠ Database not found at {db_path}")
        return None


def check_columns_exist(cursor, table_name: str, columns: list) -> dict:
    """Check which columns already exist in the table"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    existing_columns = {row[1] for row in cursor.fetchall()}
    
    result = {}
    for col in columns:
        result[col] = col in existing_columns
    
    return result


def migrate_up(db_path: str):
    """Add DLI fields to predictions table"""
    print(f"\n🔄 Starting migration: Add DLI fields to predictions table")
    print(f"   Database: {db_path}\n")
    
    # Backup database
    backup_path = backup_database(db_path)
    if not backup_path and os.path.exists(db_path):
        response = input("⚠ Backup failed. Continue anyway? (y/N): ")
        if response.lower() != 'y':
            print("Migration cancelled.")
            return False
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check which columns need to be added
        columns_to_add = [
            'dli_score',
            'dli_category',
            'mindful_score',
            'meaningful_score',
            'joyful_score',
            'pedagogis_score',
            'digital_score',
            'dli_data'
        ]
        
        existing = check_columns_exist(cursor, 'predictions', columns_to_add)
        
        # Add missing columns
        columns_added = 0
        for column in columns_to_add:
            if not existing[column]:
                if column == 'dli_data':
                    # JSON column for SQLite
                    cursor.execute(f"ALTER TABLE predictions ADD COLUMN {column} TEXT")
                elif column == 'dli_category':
                    cursor.execute(f"ALTER TABLE predictions ADD COLUMN {column} VARCHAR(64)")
                else:
                    cursor.execute(f"ALTER TABLE predictions ADD COLUMN {column} REAL")
                
                print(f"✓ Added column: {column}")
                columns_added += 1
            else:
                print(f"⊘ Column already exists: {column}")
        
        # Commit changes
        conn.commit()
        
        print(f"\n✅ Migration completed successfully!")
        print(f"   Columns added: {columns_added}")
        print(f"   Existing predictions remain unchanged (NULL for DLI fields)")
        
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Migration failed: {e}")
        print(f"   Database rolled back to previous state")
        if backup_path:
            print(f"   Backup available at: {backup_path}")
        return False
        
    finally:
        conn.close()


def migrate_down(db_path: str):
    """Remove DLI fields from predictions table (rollback)"""
    print(f"\n🔄 Rolling back migration: Remove DLI fields from predictions table")
    print(f"   Database: {db_path}\n")
    print("⚠ SQLite does not support DROP COLUMN directly.")
    print("   To rollback, restore from backup or recreate the table.")
    print("   Backup files are named: educlassify.db.backup_YYYYMMDD_HHMMSS")
    return False


def main():
    """Main migration script"""
    # Determine database path
    db_path = os.getenv("DATABASE_URL", "sqlite:///./educlassify.db")
    if db_path.startswith("sqlite:///"):
        db_path = db_path.replace("sqlite:///", "")
    
    # Check if database exists
    if not os.path.exists(db_path):
        print(f"❌ Database not found at: {db_path}")
        print("   Run the application first to create the database.")
        sys.exit(1)
    
    # Run migration
    print("=" * 70)
    print("  DLI Database Migration")
    print("=" * 70)
    
    success = migrate_up(db_path)
    
    if success:
        print("\n" + "=" * 70)
        print("  Next steps:")
        print("  1. Verify the migration by checking the predictions table")
        print("  2. Test DLI analysis with a sample document")
        print("  3. Verify existing predictions still work correctly")
        print("=" * 70)
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
