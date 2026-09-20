"""
Phase 10b -- Analytics Dashboard
===================================

Purpose:
    Show anonymized aggregate statistics from what the system has ACTUALLY
    classified so far -- never fabricated numbers, per the project brief.

Run with:
    streamlit run dashboard.py

This reads the same analytics.db that main.py writes to, so it will show
real numbers from whatever testing/demo usage has happened through the
API (or the frontend, which calls the API).
"""

import streamlit as st
import pandas as pd

from analytics_db import get_summary_stats

st.set_page_config(page_title="AI WasteWise — Analytics", page_icon="♻️", layout="centered")

st.title("AI WasteWise — Analytics")
st.caption("Anonymized aggregate statistics from real classifications made by this system. No images or personal data are stored.")

stats = get_summary_stats()

if stats["total_items_analyzed"] == 0:
    st.info(
        "No classifications logged yet. Run some images through the app "
        "(via the frontend or the /analyze endpoint) and refresh this page "
        "to see real data here."
    )
else:
    col1, col2 = st.columns(2)
    col1.metric("Total items analyzed", stats["total_items_analyzed"])
    col2.metric("Uncertain classifications", stats["uncertain_count"])

    st.subheader("Waste category distribution")
    if stats["category_distribution"]:
        cat_df = pd.DataFrame(stats["category_distribution"])
        cat_df = cat_df.rename(columns={"waste_category": "Category", "count": "Count"})
        st.bar_chart(cat_df.set_index("Category"))
    else:
        st.write("No categorized items yet (only uncertain results so far).")

    st.subheader("Most frequently detected items")
    if stats["most_frequent_items"]:
        items_df = pd.DataFrame(stats["most_frequent_items"])
        items_df = items_df.rename(columns={"detected_item": "Item", "count": "Count"})
        st.dataframe(items_df, hide_index=True, use_container_width=True)
    else:
        st.write("No items detected yet.")

st.divider()
st.caption(
    "This dashboard reflects real usage only — no simulated or placeholder "
    "numbers. If it looks sparse, that's because the system hasn't been "
    "used much yet, which is itself honest information about where this "
    "prototype currently stands."
)
