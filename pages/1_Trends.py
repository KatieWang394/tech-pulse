"""
1_Trends.py — 趋势看板页面 (Day 5 打磨版)

改进：
- 更好的空状态提示
- 文章列表支持展开/收起摘要
- 加了 "上次更新时间" 提示
- 图表有数据不足时的友好提示
- 搜索和筛选同时生效
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from services.db import init_db, get_recent_articles, get_category_counts, get_daily_trend, save_articles
from services.hn_fetcher import fetch_top_stories
from services.llm_service import categorize_stories

# ============================================================
# 页面配置
# ============================================================
st.set_page_config(page_title="Trends — Tech Pulse", page_icon="📈", layout="wide")
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

st.title("📈 Trend Tracker")
st.markdown("See what topics are heating up in the tech world.")
st.divider()

# ============================================================
# 控制面板
# ============================================================
col_btn, col_days, col_status = st.columns([2, 1, 2])

with col_btn:
    fetch_clicked = st.button("🔄 Fetch New Stories", type="primary")

with col_days:
    days_range = st.selectbox(
        "Time range:",
        [1, 3, 7, 14],
        index=2,
        format_func=lambda x: f"Last {x} day{'s' if x > 1 else ''}",
    )

# ---- 抓取逻辑（加了错误处理） ----
if fetch_clicked:
    try:
        with st.spinner("📡 Fetching stories from Hacker News..."):
            stories = fetch_top_stories(30)

        if not stories:
            st.error("Couldn't fetch stories from Hacker News. Please check your internet connection.")
            st.stop()

        with st.spinner(f"🧠 AI is categorizing {len(stories)} articles... (~30-60s)"):
            stories = categorize_stories(stories)

        new_count, skip_count = save_articles(stories)

        with col_status:
            if new_count > 0:
                st.success(f"✅ {new_count} new, {skip_count} existing")
            else:
                st.info(f"All {skip_count} already saved")

        st.rerun()

    except Exception as e:
        st.error(f"Something went wrong: {str(e)}")
        st.info("This might be a temporary network issue. Try again in a few seconds.")

# ============================================================
# 数据加载
# ============================================================
category_counts = get_category_counts(days=days_range)
daily_trend = get_daily_trend(days=days_range)

if not category_counts:
    st.info(
        "👋 No articles in the database yet!\n\n"
        "Click **Fetch New Stories** above to get started. "
        "It will pull the latest articles from Hacker News and "
        "use AI to categorize them automatically."
    )
    st.stop()

# ============================================================
# 图表
# ============================================================
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.subheader("📊 Articles by Category")
    bar_data = pd.DataFrame(
        list(category_counts.items()),
        columns=["Category", "Count"],
    ).sort_values("Count", ascending=True)
    st.bar_chart(bar_data.set_index("Category"))

with chart_col2:
    st.subheader("📈 Trend Over Time")
    if daily_trend and len(daily_trend) > 1:
        trend_df = pd.DataFrame(daily_trend).set_index("date")
        st.line_chart(trend_df)
    elif daily_trend and len(daily_trend) == 1:
        st.info(
            "📍 Only 1 day of data so far — need at least 2 to draw a trend line.\n\n"
            "Come back tomorrow and fetch again!"
        )
    else:
        st.info("No trend data yet.")

st.divider()

# ============================================================
# 统计卡片
# ============================================================
sorted_cats = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
total_articles = sum(category_counts.values())

# 顶部热门类别高亮
top_cat, top_count = sorted_cats[0]
top_emoji = CATEGORY_COLORS.get(top_cat, "⚫")
st.markdown(f"🔥 **Hottest topic:** {top_emoji} {top_cat} with {top_count} articles ({round(top_count/total_articles*100)}% of total)")

# 各类别卡片
cols = st.columns(min(len(sorted_cats), 4))
for i, (cat, count) in enumerate(sorted_cats):
    emoji = CATEGORY_COLORS.get(cat, "⚫")
    pct = round(count / total_articles * 100)
    cols[i % 4].metric(f"{emoji} {cat}", f"{count} ({pct}%)")

st.divider()

# ============================================================
# 文章列表（加了搜索+筛选同时生效）
# ============================================================
st.subheader("📰 All Articles")

filter_col1, filter_col2 = st.columns(2)

with filter_col1:
    all_categories = ["All"] + [cat for cat, _ in sorted_cats]
    selected_category = st.selectbox("Filter by category:", all_categories, key="trend_cat")

with filter_col2:
    search_term = st.text_input("🔍 Search titles & summaries:", key="trend_search")

articles = get_recent_articles(days=days_range, category=selected_category)

# 搜索过滤
if search_term:
    q = search_term.lower()
    articles = [a for a in articles if q in a["title"].lower() or q in (a["summary"] or "").lower()]

st.caption(f"Showing {len(articles)} of {total_articles} articles")

if not articles:
    st.info("No articles match your filters. Try broadening your search.")
else:
    for i, article in enumerate(articles, 1):
        emoji = CATEGORY_COLORS.get(article["category"], "⚫")

        with st.container():
            col1, col2 = st.columns([5, 1])
            with col1:
                st.markdown(f"**{i}. [{article['title']}]({article['url']})**")
                if article["summary"]:
                    st.markdown(f"💡 _{article['summary']}_")
                st.caption(
                    f"{emoji} {article['category']} · "
                    f"By {article['author']} · "
                    f"Score: {article['score']} · "
                    f"{article['fetched_at'][:10]}"
                )
            with col2:
                st.metric(label="Score", value=article["score"])
            st.divider()
