"""
1_Trends.py — 趋势看板页面

Streamlit 的多页面机制很简单：
- 放在 pages/ 文件夹下的 .py 文件会自动变成独立页面
- 文件名前面的数字（1_）控制在侧边栏里的排列顺序
- 每个页面就是一个独立的 Python 脚本

这个页面展示：
- 各类别文章数量的柱状图
- 过去几天各类别的趋势折线图
- 完整的文章列表（可筛选、可搜索）
"""

import streamlit as st
import pandas as pd
from services.db import init_db, get_recent_articles, get_category_counts, get_daily_trend
from services.hn_fetcher import fetch_top_stories
from services.llm_service import categorize_stories
from services.db import save_articles

# ============================================================
# 页面配置
# ============================================================
st.set_page_config(page_title="Trends — Tech Pulse", page_icon="📈", layout="wide")
init_db()

st.title("📈 Trend Tracker")
st.markdown("See what topics are heating up in the tech world.")
st.divider()

# ============================================================
# 控制面板
# ============================================================
col_btn, col_days = st.columns([2, 1])

with col_btn:
    fetch_clicked = st.button("🔄 Fetch New Stories", type="primary")

with col_days:
    days_range = st.selectbox("Time range:", [1, 3, 7, 14], index=2, format_func=lambda x: f"Last {x} days")

if fetch_clicked:
    with st.spinner("📡 Fetching from Hacker News..."):
        stories = fetch_top_stories(30)
    with st.spinner("🧠 AI categorizing... (~30-60s)"):
        stories = categorize_stories(stories)
    new_count, skip_count = save_articles(stories)
    if new_count > 0:
        st.success(f"✅ {new_count} new articles saved!")
    else:
        st.info(f"All {skip_count} articles already in database.")
    st.rerun()

# ============================================================
# 数据加载
# ============================================================
category_counts = get_category_counts(days=days_range)
daily_trend = get_daily_trend(days=days_range)

if not category_counts:
    st.warning("No data yet. Click 'Fetch New Stories' to get started!")
    st.stop()  # stop() 会终止页面渲染，后面的代码不会执行

# ============================================================
# 图表区域
# ============================================================
chart_col1, chart_col2 = st.columns(2)

# ---- 柱状图：各类别文章数量 ----
with chart_col1:
    st.subheader("📊 Articles by Category")

    # 把字典转成 DataFrame（Streamlit 图表需要这个格式）
    # pandas DataFrame 就是一个表格，类似 Excel 的一个 sheet
    bar_data = pd.DataFrame(
        list(category_counts.items()),
        columns=["Category", "Count"]
    ).sort_values("Count", ascending=True)  # 升序排列，这样柱状图最大的在上面

    # Streamlit 内置的柱状图
    st.bar_chart(bar_data.set_index("Category"))

# ---- 折线图：趋势变化 ----
with chart_col2:
    st.subheader("📈 Trend Over Time")

    if daily_trend:
        # daily_trend 是一个列表，每个元素类似：
        # {"date": "2026-03-25", "AI / Machine Learning": 3, "Web Development": 2}
        trend_df = pd.DataFrame(daily_trend)
        trend_df = trend_df.set_index("date")

        if len(trend_df) > 1:
            st.line_chart(trend_df)
        else:
            st.info("Need at least 2 days of data to show trends. Fetch again tomorrow!")
    else:
        st.info("No trend data available yet.")

st.divider()

# ============================================================
# 统计卡片
# ============================================================
st.subheader("🔢 Quick Stats")

sorted_cats = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
total_articles = sum(category_counts.values())

# 第一行：总数
st.metric("Total Articles", total_articles)

# 第二行：各类别
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

cols = st.columns(min(len(sorted_cats), 4))
for i, (cat, count) in enumerate(sorted_cats):
    emoji = CATEGORY_COLORS.get(cat, "⚫")
    pct = round(count / total_articles * 100)
    cols[i % 4].metric(f"{emoji} {cat}", f"{count} ({pct}%)")

st.divider()

# ============================================================
# 文章列表
# ============================================================
st.subheader("📰 All Articles")

# ---- 筛选和搜索 ----
filter_col1, filter_col2 = st.columns(2)

with filter_col1:
    all_categories = ["All"] + [cat for cat, _ in sorted_cats]
    selected_category = st.selectbox("Filter by category:", all_categories, key="trend_cat_filter")

with filter_col2:
    search_term = st.text_input("🔍 Search titles:", key="trend_search")

# ---- 加载文章 ----
articles = get_recent_articles(days=days_range, category=selected_category)

# 如果有搜索词，在 Python 里过滤（简单场景这样做就够了）
if search_term:
    search_lower = search_term.lower()
    articles = [a for a in articles if search_lower in a["title"].lower() or search_lower in (a["summary"] or "").lower()]

st.caption(f"Showing {len(articles)} articles")

# ---- 渲染列表 ----
for i, article in enumerate(articles, 1):
    emoji = CATEGORY_COLORS.get(article["category"], "⚫")

    with st.container():
        col1, col2 = st.columns([5, 1])
        with col1:
            st.markdown(f"**{i}. [{article['title']}]({article['url']})**")
            if article["summary"]:
                st.markdown(f"💡 _{article['summary']}_")
            st.caption(f"{emoji} {article['category']} · By {article['author']} · Score: {article['score']}")
        with col2:
            st.metric(label="Score", value=article["score"])
        st.divider()
