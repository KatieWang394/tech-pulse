"""
app.py — Tech Pulse 主页 (Day 4 版本)

现在 app.py 变成了一个简洁的首页 / 导航页。
具体功能拆分到了 pages/ 下的独立页面里：
- pages/1_Trends.py  → 趋势看板
- pages/2_Bookmarks.py → 个人知识库

Streamlit 多页面的工作原理：
- app.py 是首页（Home）
- pages/ 文件夹里的每个 .py 文件自动变成侧边栏里的一个页面
- 文件名前面的数字控制排序（1_ 排在 2_ 前面）
- 下划线会变成空格显示（1_Trends → "Trends"）
"""

import streamlit as st
from services.db import init_db, get_category_counts, get_bookmarks

# ============================================================
# 页面配置
# ============================================================
st.set_page_config(page_title="Tech Pulse", page_icon="⚡", layout="wide")
init_db()

# ============================================================
# 首页内容
# ============================================================
st.title("⚡ Tech Pulse")
st.markdown("Your personal tech intelligence dashboard.")
st.divider()

# ---- 快速统计 ----
col1, col2, col3 = st.columns(3)

category_counts = get_category_counts(days=7)
total_articles = sum(category_counts.values()) if category_counts else 0
total_categories = len(category_counts) if category_counts else 0
total_bookmarks = len(get_bookmarks())

col1.metric("📰 Articles Tracked", total_articles, help="From the last 7 days")
col2.metric("📊 Categories", total_categories)
col3.metric("🔖 Bookmarks Saved", total_bookmarks)

st.divider()

# ---- 导航卡片 ----
nav_col1, nav_col2 = st.columns(2)

with nav_col1:
    st.subheader("📈 Trend Tracker")
    st.markdown(
        "See what topics are trending on Hacker News. "
        "AI automatically categorizes and summarizes articles, "
        "and tracks which topics are gaining momentum."
    )
    if total_articles > 0 and category_counts:
        top_cat = max(category_counts, key=category_counts.get)
        st.markdown(f"🔥 **Top category this week:** {top_cat} ({category_counts[top_cat]} articles)")
    st.page_link("pages/1_Trends.py", label="Open Trend Tracker →", icon="📈")

with nav_col2:
    st.subheader("🔖 Knowledge Base")
    st.markdown(
        "Save any article by URL. AI generates summaries, tags, "
        "and difficulty ratings. Build your personal library of "
        "tech knowledge."
    )
    if total_bookmarks > 0:
        st.markdown(f"📚 **You have {total_bookmarks} bookmark{'s' if total_bookmarks != 1 else ''} saved**")
    st.page_link("pages/2_Bookmarks.py", label="Open Knowledge Base →", icon="🔖")

st.divider()

# ---- 页脚 ----
st.caption(
    "Built with Python · Streamlit · SQLite · Claude API · Hacker News API"
)
