"""
2_Bookmarks.py — 个人知识库页面 (Day 5 打磨版)

改进：
- 更好的错误处理和用户提示
- 可以编辑已有书签的笔记
- 从 Trends 页面一键保存文章到书签
- URL 格式验证
- 加载状态更细致
"""

import streamlit as st
from services.db import (
    init_db, save_bookmark, get_bookmarks, get_all_tags,
    delete_bookmark, update_bookmark_notes,
)
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
# 添加书签
# ============================================================
st.subheader("➕ Add a Bookmark")

with st.form("add_bookmark_form", clear_on_submit=True):
    url_input = st.text_input(
        "Paste an article URL:",
        placeholder="https://example.com/interesting-article",
    )
    notes_input = st.text_area(
        "Your notes (optional):",
        placeholder="Why did you save this? What caught your eye?",
        height=80,
    )
    submitted = st.form_submit_button("🚀 Save & Analyze", type="primary")

if submitted:
    # ---- 输入验证 ----
    if not url_input:
        st.warning("Please paste a URL first!")
    elif not url_input.startswith(("http://", "https://")):
        st.error("That doesn't look like a valid URL. Make sure it starts with http:// or https://")
    else:
        # ---- 处理流程 ----
        progress = st.empty()

        # 第一步：抓取
        progress.info("🌐 Step 1/3: Fetching article content...")
        try:
            scraped = fetch_article_content(url_input)
        except Exception as e:
            st.error(f"Network error: {str(e)}")
            scraped = {"success": False, "content": str(e), "title": "Error"}

        if not scraped["success"]:
            progress.empty()
            st.error(f"❌ Couldn't fetch that URL.")
            st.info(
                "**Possible reasons:**\n"
                "- The website might block automated access\n"
                "- The URL might be behind a login wall\n"
                "- The page might be temporarily down\n\n"
                "**Try:** a different article, or a blog/news site URL."
            )
        else:
            # 第二步：AI 分析
            progress.info("🧠 Step 2/3: AI analyzing content...")
            try:
                analysis = summarize_bookmark(scraped["title"], scraped["content"])
            except Exception as e:
                st.error(f"AI analysis failed: {str(e)}")
                analysis = {"summary": "Analysis failed", "tags": "untagged", "difficulty": "intermediate"}

            # 第三步：保存
            progress.info("💾 Step 3/3: Saving to database...")
            success = save_bookmark(
                url=url_input,
                title=scraped["title"],
                content_snippet=scraped["content"][:500],
                summary=analysis["summary"],
                tags=analysis["tags"],
                difficulty=analysis["difficulty"],
                user_notes=notes_input,
            )

            progress.empty()

            if success:
                st.success(f"✅ Saved: **{scraped['title']}**")
                # 预览结果
                with st.container():
                    st.markdown(f"📝 **Summary:** {analysis['summary']}")
                    tags_display = " ".join([f"`{t.strip()}`" for t in analysis["tags"].split(",")])
                    st.markdown(f"🏷️ **Tags:** {tags_display}")
                    diff_emoji = {"beginner": "🟢", "intermediate": "🟡", "advanced": "🔴"}
                    st.markdown(f"📊 **Difficulty:** {diff_emoji.get(analysis['difficulty'], '⚪')} {analysis['difficulty']}")
                st.rerun()
            else:
                st.error("Failed to save. Please try again.")

st.divider()

# ============================================================
# 搜索和筛选
# ============================================================
st.subheader("📚 Your Bookmarks")

filter_col1, filter_col2 = st.columns(2)

with filter_col1:
    search_query = st.text_input("🔍 Search:", placeholder="Search titles, summaries, or tags...")

with filter_col2:
    all_tags = get_all_tags()
    tag_options = ["All tags"] + all_tags
    selected_tag = st.selectbox("🏷️ Filter by tag:", tag_options)

# ---- 查询 ----
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
        diff_emoji = {"beginner": "🟢", "intermediate": "🟡", "advanced": "🔴"}
        emoji = diff_emoji.get(bookmark["difficulty"], "⚪")

        with st.container():
            # ---- 标题行 + 删除 ----
            header_col, action_col = st.columns([6, 1])
            with header_col:
                st.markdown(f"### [{bookmark['title']}]({bookmark['url']})")
            with action_col:
                if st.button("🗑️", key=f"del_{bookmark['id']}", help="Delete"):
                    delete_bookmark(bookmark["id"])
                    st.rerun()

            # ---- 摘要 ----
            st.markdown(f"📝 {bookmark['summary']}")

            # ---- 标签 + 难度 ----
            info_col1, info_col2 = st.columns([3, 1])
            with info_col1:
                if bookmark["tags"] and bookmark["tags"] != "untagged":
                    tags = bookmark["tags"].split(",")
                    tag_display = " ".join([f"`{tag.strip()}`" for tag in tags])
                    st.markdown(f"🏷️ {tag_display}")
            with info_col2:
                st.markdown(f"{emoji} **{bookmark['difficulty']}**")

            # ---- 笔记（可编辑） ----
            # 用 expander 折叠起来，保持页面整洁
            with st.expander("📌 Notes", expanded=bool(bookmark["user_notes"])):
                current_notes = bookmark["user_notes"] or ""
                new_notes = st.text_area(
                    "Your notes:",
                    value=current_notes,
                    key=f"notes_{bookmark['id']}",
                    height=80,
                    label_visibility="collapsed",
                )
                if new_notes != current_notes:
                    if st.button("💾 Save notes", key=f"save_notes_{bookmark['id']}"):
                        update_bookmark_notes(bookmark["id"], new_notes)
                        st.success("Notes saved!")
                        st.rerun()

            st.caption(f"Saved on {bookmark['saved_at'][:10]}")
            st.divider()
else:
    if search_query or selected_tag != "All tags":
        st.info("No bookmarks match your search. Try different keywords.")
    else:
        st.markdown(
            "### 👋 Your knowledge base is empty!\n\n"
            "Paste a URL above to save your first article. Here are some ideas:\n\n"
            "- A blog post you found insightful\n"
            "- A tutorial you want to reference later\n"
            "- A news article about a tech trend you're following\n"
        )
