"""Reset stuck/processing jobs back to failed so they can be retried."""
import sqlite3, os

db = os.path.join(os.path.dirname(__file__), '..', '..', 'educlassify.db')
db = os.path.abspath(db)
conn = sqlite3.connect(db)
c = conn.cursor()

c.execute("SELECT job_id, status FROM video_analysis_jobs WHERE status IN ('processing','queued')")
rows = c.fetchall()
print(f"Found {len(rows)} stuck jobs")

for job_id, status in rows:
    c.execute(
        "UPDATE video_analysis_jobs SET status='failed', stage='failed', progress=0.0, error_msg='Reset - pipeline diperbarui.' WHERE job_id=?",
        (job_id,)
    )
    # Delete partial results
    for tbl in ('video_analysis_results', 'video_fragments', 'evidence_clips', 'triangulation_results'):
        c.execute(f"DELETE FROM {tbl} WHERE job_id=?", (job_id,))
    print(f"  Reset {job_id[:8]}... ({status})")

conn.commit()
conn.close()
print("Done.")
