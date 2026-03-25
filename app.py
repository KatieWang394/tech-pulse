"""
app.py — Tech Pulse 的主页面

运行方式：在终端输入 streamlit run app.py
然后浏览器会自动打开 http://localhost:8501

Day 1 版本：先做一个简单的页面，点按钮就能看到 HN 热门文章。
后面几天会慢慢加上 AI 分类、数据库、图表等功能。
"""

import streamlit as st
from services.hn_fetcher import fetch_top_stories


# ============================================================
# 页面配置 — 必须是 Streamlit 代码的第一行
# ============================================================
st.set_page_config(
    page_title="Tech Pulse",
    page_icon="⚡",
    layout="wide",
)

# ============================================================
# 标题和介绍
# ============================================================
st.title("⚡ Tech Pulse")
st.markdown("Your personal tech intelligence dashboard — track what's trending, save what matters.")
st.divider()

# ============================================================
# 获取数据的按钮
# ============================================================
# st.session_state 是 Streamlit 的 "记忆" 功能
# 因为每次你点击按钮，Streamlit 会重新运行整个脚本
# 如果不把数据存在 session_state 里，数据就丢了
# 这个概念一开始可能有点奇怪，但用一两次就习惯了
if "stories" not in st.session_state:
    st.session_state.stories = []

if st.button("🔄 Fetch Latest from Hacker News", type="primary"):
    with st.spinner("Fetching stories from Hacker News..."):
        st.session_state.stories = fetch_top_stories(30)
    st.success(f"Fetched {len(st.session_state.stories)} stories!")

# ============================================================
# 显示文章列表
# ============================================================
if st.session_state.stories:
    st.subheader(f"Top {len(st.session_state.stories)} Stories")

    for i, story in enumerate(st.session_state.stories, 1):
        # st.container 创建一个可视化的 "卡片" 区域
        with st.container():
            col1, col2 = st.columns([5, 1])
            with col1:
                st.markdown(f"**{i}. [{story['title']}]({story['url']})**")
                st.caption(f"By {story['author']} · {story['num_comments']} comments")
            with col2:
                st.metric(label="Score", value=story["score"])
            st.divider()
else:
    st.info("👆 Click the button above to fetch the latest stories from Hacker News!")
    st.markdown("---")
    st.markdown(
        "**Coming soon:** AI-powered categorization, trend tracking, "
        "and your personal knowledge base. Stay tuned!"
    )
