"""
app.py — Tech Pulse 主页面 (Day 2 版本)

更新内容：
- 加上了 AI 自动分类和摘要功能
- 文章按类别显示，带颜色标签
- 加了简单的统计信息
"""

import streamlit as st
from services.hn_fetcher import fetch_top_stories
from services.llm_service import categorize_stories

# ============================================================
# 页面配置
# ============================================================
st.set_page_config(
    page_title="Tech Pulse",
    page_icon="⚡",
    layout="wide",
)

# ============================================================
# 类别对应的颜色 — 用于显示标签
# 这些是 Streamlit 支持的 markdown 颜色写法
# ============================================================
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
# Session state 初始化
# ============================================================
if "stories" not in st.session_state:
    st.session_state.stories = []

# ============================================================
# 获取 + 分类按钮
# ============================================================
col_btn, col_info = st.columns([2, 3])
with col_btn:
    fetch_clicked = st.button("🔄 Fetch & Analyze Latest Stories", type="primary")
with col_info:
    if st.session_state.stories:
        st.caption(f"Currently showing {len(st.session_state.stories)} stories")
    else:
        st.caption("Click to fetch stories from Hacker News and auto-categorize with AI")

if fetch_clicked:
    # 第一步：从 HN 拿数据（你昨天写的）
    with st.spinner("📡 Fetching stories from Hacker News..."):
        stories = fetch_top_stories(30)

    # 第二步：用 Claude API 分类（今天新加的！）
    with st.spinner("🧠 AI is categorizing and summarizing articles... (this takes about 30-60 seconds)"):
        stories = categorize_stories(stories)

    st.session_state.stories = stories
    st.success(f"Done! Fetched and analyzed {len(stories)} stories.")
    st.rerun()  # 刷新页面以显示新数据

# ============================================================
# 显示结果
# ============================================================
if st.session_state.stories:
    stories = st.session_state.stories

    # ---- 统计面板 ----
    st.subheader("📊 Category Breakdown")

    # 统计每个类别有多少篇文章
    category_counts = {}
    for s in stories:
        cat = s.get("category", "Other")
        category_counts[cat] = category_counts.get(cat, 0) + 1

    # 按数量排序
    sorted_cats = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)

    # 用 columns 横向显示各类别的数量
    cols = st.columns(min(len(sorted_cats), 4))
    for i, (cat, count) in enumerate(sorted_cats):
        emoji = CATEGORY_COLORS.get(cat, "⚫")
        cols[i % 4].metric(f"{emoji} {cat}", count)

    st.divider()

    # ---- 筛选器 ----
    st.subheader("📰 Articles")

    # 类别筛选
    all_categories = ["All"] + [cat for cat, _ in sorted_cats]
    selected_category = st.selectbox("Filter by category:", all_categories)

    # 根据筛选条件过滤文章
    filtered = stories
    if selected_category != "All":
        filtered = [s for s in stories if s.get("category") == selected_category]

    st.caption(f"Showing {len(filtered)} articles")

    # ---- 文章列表 ----
    for i, story in enumerate(filtered, 1):
        emoji = CATEGORY_COLORS.get(story.get("category", "Other"), "⚫")

        with st.container():
            # 第一行：标题 + 分数
            col1, col2 = st.columns([5, 1])
            with col1:
                st.markdown(f"**{i}. [{story['title']}]({story['url']})**")
                # 第二行：AI 摘要
                st.markdown(f"💡 _{story.get('summary', 'No summary')}_")
                # 第三行：元信息
                st.caption(
                    f"{emoji} {story.get('category', 'Other')} · "
                    f"By {story['author']} · "
                    f"{story['num_comments']} comments"
                )
            with col2:
                st.metric(label="Score", value=story["score"])

            st.divider()

else:
    st.info("👆 Click the button above to fetch and analyze the latest stories from Hacker News!")

    # 展示一下功能预告
    st.markdown("### What this does:")
    st.markdown(
        "1. **Fetches** the top 30 stories from Hacker News\n"
        "2. **Categorizes** each article using Claude AI (AI, Web Dev, Security, etc.)\n"
        "3. **Summarizes** each article in one sentence\n"
        "4. **Displays** everything with filtering and stats"
    )
