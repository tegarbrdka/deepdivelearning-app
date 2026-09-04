"""
Migration: Add 3M Video Analysis tables

This migration creates 6 new tables to support the Advanced Video Analysis
(3M Pedagogy) feature. It is additive only — no existing tables are modified.

Tables created:
  - video_analysis_jobs
  - video_analysis_results
  - video_fragments
  - evidence_clips
  - lesson_plans
  - triangulation_results

Usage:
    python backend/migrations/002_add_video_analysis_3m.py

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


def table_exists(cursor, table_name: str) -> bool:
    """Check whether a table already exists in the database"""
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,)
    )
    return cursor.fetchone() is not None


def migrate_up(db_path: str):
    """Create the 6 new 3M video analysis tables"""
    print(f"\n🔄 Starting migration: Add 3M Video Analysis tables")
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
        tables_created = 0

        # ------------------------------------------------------------------
        # 1. video_analysis_jobs
        # ------------------------------------------------------------------
        table_name = "video_analysis_jobs"
        if not table_exists(cursor, table_name):
            cursor.execute("""
                CREATE TABLE video_analysis_jobs (
                    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id              TEXT    UNIQUE NOT NULL,
                    user_id             INTEGER REFERENCES users(id),
                    video_path          TEXT    NOT NULL,
                    video_name          TEXT,
                    rpp_path            TEXT,
                    status              TEXT    DEFAULT 'queued',
                    stage               TEXT,
                    progress            REAL    DEFAULT 0.0,
                    error_msg           TEXT,
                    video_duration_sec  REAL,
                    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
                    completed_at        DATETIME
                )
            """)
            print(f"✓ Created table: {table_name}")
            tables_created += 1
        else:
            print(f"⊘ Table already exists: {table_name}")

        # ------------------------------------------------------------------
        # 2. video_analysis_results
        # ------------------------------------------------------------------
        table_name = "video_analysis_results"
        if not table_exists(cursor, table_name):
            cursor.execute("""
                CREATE TABLE video_analysis_results (
                    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id                  TEXT    UNIQUE REFERENCES video_analysis_jobs(job_id),
                    mindful_score           REAL,
                    meaningful_score        REAL,
                    joyful_score            REAL,
                    overall_3m_score        REAL,
                    gaze_score              REAL,
                    posture_score           REAL,
                    silence_quality_score   REAL,
                    seating_score           REAL,
                    talk_time_score         REAL,
                    question_type_score     REAL,
                    teacher_movement_score  REAL,
                    expression_score        REAL,
                    acoustic_score          REAL,
                    collaboration_score     REAL,
                    risk_taking_score       REAL,
                    teacher_talk_pct        REAL,
                    student_talk_pct        REAL,
                    silence_pct             REAL,
                    meets_dl_standard       INTEGER,
                    timeline_data           TEXT,
                    heatmap_data            TEXT,
                    aha_moments             TEXT,
                    laughter_events         TEXT,
                    applause_events         TEXT,
                    seating_transitions     TEXT,
                    recommendations         TEXT,
                    created_at              DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print(f"✓ Created table: {table_name}")
            tables_created += 1
        else:
            print(f"⊘ Table already exists: {table_name}")

        # ------------------------------------------------------------------
        # 3. video_fragments
        # ------------------------------------------------------------------
        table_name = "video_fragments"
        if not table_exists(cursor, table_name):
            cursor.execute("""
                CREATE TABLE video_fragments (
                    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id                  TEXT    REFERENCES video_analysis_jobs(job_id),
                    fragment_index          INTEGER,
                    start_sec               REAL,
                    end_sec                 REAL,
                    mindful_score           REAL,
                    meaningful_score        REAL,
                    joyful_score            REAL,
                    gaze_score              REAL,
                    posture_score           REAL,
                    silence_quality_score   REAL,
                    seating_score           REAL,
                    talk_time_score         REAL,
                    question_type_score     REAL,
                    teacher_movement_score  REAL,
                    expression_score        REAL,
                    acoustic_score          REAL,
                    collaboration_score     REAL,
                    seating_formation       TEXT,
                    active_zone_ratio       REAL,
                    teacher_talk_pct        REAL,
                    student_talk_pct        REAL,
                    created_at              DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print(f"✓ Created table: {table_name}")
            tables_created += 1
        else:
            print(f"⊘ Table already exists: {table_name}")

        # ------------------------------------------------------------------
        # 4. evidence_clips
        # ------------------------------------------------------------------
        table_name = "evidence_clips"
        if not table_exists(cursor, table_name):
            cursor.execute("""
                CREATE TABLE evidence_clips (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id      TEXT    REFERENCES video_analysis_jobs(job_id),
                    result_id   INTEGER REFERENCES video_analysis_results(id),
                    clip_path   TEXT,
                    clip_name   TEXT,
                    start_sec   REAL,
                    end_sec     REAL,
                    clip_type   TEXT,
                    aspect      TEXT,
                    description TEXT,
                    score       REAL,
                    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print(f"✓ Created table: {table_name}")
            tables_created += 1
        else:
            print(f"⊘ Table already exists: {table_name}")

        # ------------------------------------------------------------------
        # 5. lesson_plans
        # ------------------------------------------------------------------
        table_name = "lesson_plans"
        if not table_exists(cursor, table_name):
            cursor.execute("""
                CREATE TABLE lesson_plans (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id     INTEGER NOT NULL REFERENCES users(id),
                    file_path   TEXT    NOT NULL,
                    file_name   TEXT,
                    parsed_data TEXT,
                    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print(f"✓ Created table: {table_name}")
            tables_created += 1
        else:
            print(f"⊘ Table already exists: {table_name}")

        # ------------------------------------------------------------------
        # 6. triangulation_results
        # ------------------------------------------------------------------
        table_name = "triangulation_results"
        if not table_exists(cursor, table_name):
            cursor.execute("""
                CREATE TABLE triangulation_results (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id          TEXT    UNIQUE REFERENCES video_analysis_jobs(job_id),
                    result_id       INTEGER UNIQUE REFERENCES video_analysis_results(id),
                    items           TEXT,
                    alignment_score REAL,
                    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print(f"✓ Created table: {table_name}")
            tables_created += 1
        else:
            print(f"⊘ Table already exists: {table_name}")

        # Commit all changes
        conn.commit()

        print(f"\n✅ Migration completed successfully!")
        print(f"   Tables created: {tables_created}")

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
    """Drop the 3M video analysis tables (rollback)"""
    print(f"\n🔄 Rolling back migration: Remove 3M Video Analysis tables")
    print(f"   Database: {db_path}\n")
    print("⚠ SQLite does not support DROP TABLE with foreign-key safety easily.")
    print("   To rollback, restore from backup or drop tables manually.")
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
    print("  3M Video Analysis Database Migration")
    print("=" * 70)

    success = migrate_up(db_path)

    if success:
        print("\n" + "=" * 70)
        print("  Next steps:")
        print("  1. Verify the migration by inspecting the new tables")
        print("  2. Restart the backend so SQLAlchemy picks up the new models")
        print("  3. Test a sample video analysis job end-to-end")
        print("=" * 70)
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
