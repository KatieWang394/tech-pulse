"""
app.py — Tech Pulse 首页 (Day 5 打磨版)

改进：
- 更清晰的数据统计
- 最近保存的书签预览
- 热门类别高亮
"""

import streamlit as st
from services.db import init_db, get_category_counts, get_bookmarks, get_recent_articles

# ============================================================
# 页面配置
# ============================================================
st.set_page_config(page_title="Tech Pulse", page_icon="⚡", layout="wide")
init_db()

# ============================================================
# 首页
# ============================================================
st.title("⚡ Tech Pulse")
st.markdown("Your personal tech intelligence dashboard.")
st.divider()

# ---- 数据加载 ----
category_counts = get_category_counts(days=7)
total_articles = sum(category_counts.values()) if category_counts else 0
total_categories = len(category_counts) if category_counts else 0
bookmarks = get_bookmarks()
total_bookmarks = len(bookmarks)

# ---- 统计卡片 ----
col1, col2, col3 = st.columns(3)
col1.metric("📰 Articles Tracked", total_articles, help="From the last 7 days")
col2.metric("📊 Categories", total_categories)
col3.metric("🔖 Bookmarks Saved", total_bookmarks)

st.divider()

# ---- 两栏导航 ----
nav_col1, nav_col2 = st.columns(2)

with nav_col1:
    st.subheader("📈 Trend Tracker")
    if total_articles > 0 and category_counts:
        top_cat = max(category_counts, key=category_counts.get)
        st.markdown(f"🔥 **Top category this week:** {top_cat} ({category_counts[top_cat]} articles)")

        # 显示前 3 个类别
        sorted_cats = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        for cat, count in sorted_cats:
            pct = round(count / total_articles * 100)
            st.progress(pct / 100, text=f"{cat}: {count} articles ({pct}%)")
    else:
        st.markdown("No data yet — click below to start tracking!")

    st.page_link("pages/1_Trends.py", label="Open Trend Tracker →", icon="📈")

with nav_col2:
    st.subheader("🔖 Knowledge Base")
    if total_bookmarks > 0:
        st.markdown(f"📚 **{total_bookmarks} article{'s' if total_bookmarks != 1 else ''} saved**")

        # 显示最近 3 个书签
        st.markdown("**Recent saves:**")
        for b in bookmarks[:3]:
            st.markdown(f"- [{b['title'][:50]}{'...' if len(b['title']) > 50 else ''}]({b['url']})")
    else:
        st.markdown("Start building your personal library — save articles and get AI summaries!")

    st.page_link("pages/2_Bookmarks.py", label="Open Knowledge Base →", icon="🔖")

st.divider()

# ---- 页脚 ----
st.caption("Built with Python · Streamlit · SQLite · Claude API · Hacker News API")
