"""
app.py — Tech Pulse 主页面 (Day 3 版本)

更新内容：
- 文章现在存进 SQLite 数据库了（不用每次重新抓+分析）
- 加了 "已有数据" 和 "新抓取" 的区分
- 显示新增/跳过的文章数量
"""

import streamlit as st
from services.hn_fetcher import fetch_top_stories
from services.llm_service import categorize_stories
from services.db import init_db, save_articles, get_recent_articles, get_category_counts

# ============================================================
# 初始化
# ============================================================
st.set_page_config(page_title="Tech Pulse", page_icon="⚡", layout="wide")

# 确保数据库表存在（安全地多次调用）
init_db()

CATEGORY_COLORS = {
    "AI / Machine Learning": "🟣",
    "Web Development": "🔵",
    "Security / Privacy": "🔴",
    "DevOps / Infrastructure": "🟠",
    "Programming Languages": "🟢",
    "Startups / Business": "🟡",
    "Science / Research": "⚪",
    "Career / Industry": "🟤",
    "Other": "⚫",
}

# ============================================================
# 标题
# ============================================================
st.title("⚡ Tech Pulse")
st.markdown("Your personal tech intelligence dashboard — track what's trending, save what matters.")
st.divider()

# ============================================================
# 控制面板
# ============================================================
col_btn, col_days, col_info = st.columns([2, 1, 2])

with col_btn:
    fetch_clicked = st.button("🔄 Fetch & Analyze New Stories", type="primary")

with col_days:
    days_range = st.selectbox("Time range:", [1, 3, 7], index=2, format_func=lambda x: f"Last {x} day{'s' if x > 1 else ''}")

# ---- 抓取新数据 ----
if fetch_clicked:
    with st.spinner("📡 Fetching stories from Hacker News..."):
        stories = fetch_top_stories(30)

    with st.spinner("🧠 AI is categorizing... (~30-60 seconds)"):
        stories = categorize_stories(stories)

    new_count, skip_count = save_articles(stories)

    with col_info:
        if new_count > 0:
            st.success(f"✅ {new_count} new articles saved, {skip_count} already in database")
        else:
            st.info(f"All {skip_count} articles were already in database. Try again later for new stories!")

# ============================================================
# 从数据库读取并显示（不管有没有点抓取按钮）
# ============================================================
category_counts = get_category_counts(days=days_range)

if category_counts:
    # ---- 统计面板 ----
    st.subheader("📊 Category Breakdown")

    sorted_cats = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
    cols = st.columns(min(len(sorted_cats), 4))
    for i, (cat, count) in enumerate(sorted_cats):
        emoji = CATEGORY_COLORS.get(cat, "⚫")
        cols[i % 4].metric(f"{emoji} {cat}", count)

    st.divider()

    # ---- 文章列表 ----
    st.subheader("📰 Articles")

    all_categories = ["All"] + [cat for cat, _ in sorted_cats]
    selected_category = st.selectbox("Filter by category:", all_categories)

    articles = get_recent_articles(days=days_range, category=selected_category)
    st.caption(f"Showing {len(articles)} articles from the last {days_range} day{'s' if days_range > 1 else ''}")

    for i, article in enumerate(articles, 1):
        emoji = CATEGORY_COLORS.get(article["category"], "⚫")

        with st.container():
            col1, col2 = st.columns([5, 1])
            with col1:
                st.markdown(f"**{i}. [{article['title']}]({article['url']})**")
                st.markdown(f"💡 _{article['summary'] or 'No summary'}_")
                st.caption(
                    f"{emoji} {article['category']} · "
                    f"By {article['author']} · "
                    f"Score: {article['score']}"
                )
            with col2:
                st.metric(label="Score", value=article["score"])
            st.divider()

else:
    st.info("👆 Click 'Fetch & Analyze' to get started! Articles will be saved to the database so you don't have to re-fetch every time.")
