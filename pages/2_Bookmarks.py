"""
2_Bookmarks.py — 个人知识库页面

功能：
- 粘贴 URL → 自动抓取内容 → AI 生成摘要和标签 → 存入数据库
- 按标签筛选、关键词搜索
- 查看、添加笔记、删除书签
"""

import streamlit as st
from services.db import init_db, save_bookmark, get_bookmarks, get_all_tags, delete_bookmark
from services.web_scraper import fetch_article_content
from services.llm_service import summarize_bookmark

# ============================================================
# 页面配置
# ============================================================
st.set_page_config(page_title="Bookmarks — Tech Pulse", page_icon="🔖", layout="wide")
init_db()

st.title("🔖 Knowledge Base")
st.markdown("Save articles, get AI summaries, and build your personal library.")
st.divider()

# ============================================================
# 添加书签区域
# ============================================================
st.subheader("➕ Add a Bookmark")

with st.form("add_bookmark_form", clear_on_submit=True):
    url_input = st.text_input(
        "Paste an article URL:",
        placeholder="https://example.com/interesting-article"
    )
    notes_input = st.text_area(
        "Your notes (optional):",
        placeholder="Why did you save this? Any key takeaways?",
        height=80,
    )
    submitted = st.form_submit_button("🚀 Save & Analyze", type="primary")

if submitted and url_input:
    # ---- 第一步：抓取网页内容 ----
    with st.spinner("🌐 Fetching article content..."):
        scraped = fetch_article_content(url_input)

    if not scraped["success"]:
        st.error(f"Couldn't fetch that URL: {scraped['content']}")
        st.info("Tip: Some websites block automated access. Try a different article.")
    else:
        # ---- 第二步：AI 分析 ----
        with st.spinner("🧠 AI is reading and analyzing the article..."):
            analysis = summarize_bookmark(scraped["title"], scraped["content"])

        # ---- 第三步：存入数据库 ----
        success = save_bookmark(
            url=url_input,
            title=scraped["title"],
            content_snippet=scraped["content"][:500],
            summary=analysis["summary"],
            tags=analysis["tags"],
            difficulty=analysis["difficulty"],
            user_notes=notes_input,
        )

        if success:
            st.success(f"✅ Saved: **{scraped['title']}**")

            # 显示 AI 分析结果的预览
            preview_col1, preview_col2 = st.columns([3, 1])
            with preview_col1:
                st.markdown(f"**Summary:** {analysis['summary']}")
                st.markdown(f"**Tags:** {analysis['tags']}")
            with preview_col2:
                difficulty_emoji = {"beginner": "🟢", "intermediate": "🟡", "advanced": "🔴"}
                st.markdown(f"**Difficulty:** {difficulty_emoji.get(analysis['difficulty'], '⚪')} {analysis['difficulty']}")
            st.rerun()
        else:
            st.error("Something went wrong saving the bookmark. Please try again.")

elif submitted and not url_input:
    st.warning("Please paste a URL first!")

st.divider()

# ============================================================
# 搜索和筛选
# ============================================================
st.subheader("📚 Your Bookmarks")

filter_col1, filter_col2 = st.columns(2)

with filter_col1:
    search_query = st.text_input("🔍 Search:", placeholder="Search by title, summary, or tags...")

with filter_col2:
    all_tags = get_all_tags()
    tag_options = ["All tags"] + all_tags
    selected_tag = st.selectbox("🏷️ Filter by tag:", tag_options)

# ---- 查询书签 ----
if search_query:
    bookmarks = get_bookmarks(search_query=search_query)
elif selected_tag != "All tags":
    bookmarks = get_bookmarks(tag_filter=selected_tag)
else:
    bookmarks = get_bookmarks()

st.caption(f"{len(bookmarks)} bookmark{'s' if len(bookmarks) != 1 else ''}")

# ============================================================
# 书签列表
# ============================================================
if bookmarks:
    for bookmark in bookmarks:
        difficulty_emoji = {"beginner": "🟢", "intermediate": "🟡", "advanced": "🔴"}
        emoji = difficulty_emoji.get(bookmark["difficulty"], "⚪")

        with st.container():
            # 标题行
            header_col, delete_col = st.columns([6, 1])
            with header_col:
                st.markdown(f"### [{bookmark['title']}]({bookmark['url']})")
            with delete_col:
                # 每个删除按钮需要一个独一无二的 key，不然 Streamlit 会报错
                if st.button("🗑️", key=f"del_{bookmark['id']}", help="Delete this bookmark"):
                    delete_bookmark(bookmark["id"])
                    st.rerun()

            # 摘要
            st.markdown(f"📝 {bookmark['summary']}")

            # 标签和元信息
            info_col1, info_col2 = st.columns([3, 1])
            with info_col1:
                # 把逗号分隔的标签变成好看的标签样式
                if bookmark["tags"] and bookmark["tags"] != "untagged":
                    tags = bookmark["tags"].split(",")
                    tag_display = " ".join([f"`{tag.strip()}`" for tag in tags])
                    st.markdown(f"🏷️ {tag_display}")
            with info_col2:
                st.markdown(f"{emoji} **{bookmark['difficulty']}**")

            # 用户笔记
            if bookmark["user_notes"]:
                st.info(f"📌 **Your notes:** {bookmark['user_notes']}")

            # 保存时间
            st.caption(f"Saved on {bookmark['saved_at'][:10]}")

            st.divider()
else:
    if search_query or selected_tag != "All tags":
        st.info("No bookmarks match your search. Try different keywords or clear the filter.")
    else:
        st.info(
            "No bookmarks yet! Paste a URL above to save your first article.\n\n"
            "**Ideas for what to bookmark:**\n"
            "- Articles you want to read later\n"
            "- Tutorials you found helpful\n"
            "- Blog posts about tech trends\n"
            "- Documentation you keep coming back to"
        )
