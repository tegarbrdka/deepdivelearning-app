"""
Migration 003: Add discussion_groups_count to video_analysis_results
"""
import sqlite3
import os


def run():
    db_path = os.path.join(os.path.dirname(__file__), "..", "educlassify.db")
    db_path = os.path.abspath(db_path)

    if not os.path.exists(db_path):
        print(f"[Migration 003] DB not found at {db_path}, skipping.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if column already exists
    cursor.execute("PRAGMA table_info(video_analysis_results)")
    columns = [row[1] for row in cursor.fetchall()]

    if "discussion_groups_count" not in columns:
        cursor.execute(
            "ALTER TABLE video_analysis_results ADD COLUMN discussion_groups_count INTEGER DEFAULT 0"
        )
        conn.commit()
        print("[Migration 003] Added discussion_groups_count column.")
    else:
        print("[Migration 003] Column already exists, skipping.")

    conn.close()


if __name__ == "__main__":
    run()
