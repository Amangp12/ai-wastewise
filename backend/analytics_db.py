"""
Phase 10a -- Analytics Storage
=================================

Purpose:
    Log an anonymized record of every classification the system makes,
    so the dashboard (Phase 10b) can show REAL aggregate statistics --
    never fabricated numbers, per the project brief's explicit rule.

Privacy note (Responsible AI -- Privacy):
    We deliberately store the MINIMUM needed for aggregate stats:
    - detected item name (short text, not the image)
    - waste category
    - whether the result was grounded in the RAG sources
    - whether it was an "uncertain" result
    - a timestamp
    We do NOT store: the uploaded image, any user identifier, IP address,
    or session information. There is nothing in this table that
    identifies who submitted a given item.
"""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent / "analytics.db"


def init_db():
    """Create the analytics table if it doesn't exist yet. Safe to call on every startup."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS classification_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            detected_item TEXT,
            waste_category TEXT NOT NULL,
            grounded_in_sources INTEGER,
            is_uncertain INTEGER NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def log_result(detected_item: str, waste_category: str, grounded_in_sources: bool, is_uncertain: bool):
    """Log one anonymized classification result."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        INSERT INTO classification_log
            (timestamp, detected_item, waste_category, grounded_in_sources, is_uncertain)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            datetime.now(timezone.utc).isoformat(),
            detected_item,
            waste_category,
            int(grounded_in_sources),
            int(is_uncertain),
        ),
    )
    conn.commit()
    conn.close()


def get_summary_stats() -> dict:
    """Compute real aggregate stats from whatever has actually been logged so far.
    Returns zeroed-out stats if nothing has been logged yet -- never invents numbers.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    total = conn.execute("SELECT COUNT(*) AS c FROM classification_log").fetchone()["c"]
    uncertain_count = conn.execute(
        "SELECT COUNT(*) AS c FROM classification_log WHERE is_uncertain = 1"
    ).fetchone()["c"]

    category_rows = conn.execute("""
        SELECT waste_category, COUNT(*) AS count
        FROM classification_log
        WHERE is_uncertain = 0
        GROUP BY waste_category
        ORDER BY count DESC
    """).fetchall()

    top_items_rows = conn.execute("""
        SELECT detected_item, COUNT(*) AS count
        FROM classification_log
        WHERE is_uncertain = 0 AND detected_item IS NOT NULL AND detected_item != ''
        GROUP BY detected_item
        ORDER BY count DESC
        LIMIT 10
    """).fetchall()

    conn.close()

    return {
        "total_items_analyzed": total,
        "uncertain_count": uncertain_count,
        "category_distribution": [dict(r) for r in category_rows],
        "most_frequent_items": [dict(r) for r in top_items_rows],
    }


# Ensure the table exists as soon as this module is imported.
init_db()
