"""
llm_service.py — 用 Claude API 对文章进行分类和摘要 (Day 6 部署兼容版)

改动：
- 同时支持 .env（本地开发）和 Streamlit secrets（云端部署）
- 加了你之前发现的 JSON 清理 fix
"""

import os
import json
from anthropic import Anthropic
from dotenv import load_dotenv

# 加载 .env 文件（本地开发用）
load_dotenv()


def get_api_key():
    """
    获取 API key，按优先级尝试：
    1. Streamlit secrets（部署到 Streamlit Cloud 时用这个）
    2. 环境变量 / .env 文件（本地开发时用这个）
    """
    # 先试 Streamlit secrets
    try:
        import streamlit as st
        if "ANTHROPIC_API_KEY" in st.secrets:
            return st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        pass

    # 再试环境变量
    key = os.getenv("ANTHROPIC_API_KEY")
    if key:
        return key

    raise ValueError(
        "No API key found! Either:\n"
        "- Create a .env file with ANTHROPIC_API_KEY=your_key (local dev)\n"
        "- Add it to Streamlit secrets (cloud deployment)"
    )
def get_api_key():
    """
    获取 API key，按优先级尝试：
    1. 环境变量 / .env 文件（本地开发）
    2. Streamlit secrets（云端部署）
    """
    # 先试环境变量（本地开发不会触发警告）
    key = os.getenv("ANTHROPIC_API_KEY")
    if key:
        return key

    # 再试 Streamlit secrets（云端部署时用）
    try:
        import streamlit as st
        if "ANTHROPIC_API_KEY" in st.secrets:
            return st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        pass

    raise ValueError(
        "No API key found! Either:\n"
        "- Create a .env file with ANTHROPIC_API_KEY=your_key (local dev)\n"
        "- Add it to Streamlit secrets (cloud deployment)"
    )

client = None

def get_client():
    global client
    if client is None:
        client = Anthropic(api_key=get_api_key())
    return client

# ============================================================
# 分类列表
# ============================================================
CATEGORIES = [
    "AI / Machine Learning",
    "Web Development",
    "Security / Privacy",
    "DevOps / Infrastructure",
    "Programming Languages",
    "Startups / Business",
    "Science / Research",
    "Career / Industry",
    "Other",
]


def clean_json_response(text):
    """清理 Claude 返回的 JSON（去掉可能的 ```json ``` 包裹）"""
    text = text.strip()
    text = text.replace("```json", "").replace("```", "").strip()
    return text


# ============================================================
# 给 HN 文章分类 + 生成摘要
# ============================================================
def categorize_article(title, url):
    system_prompt = """You are a tech news classifier. Given an article title and URL, you must:
1. Classify it into exactly ONE of these categories: """ + ", ".join(CATEGORIES) + """
2. Write a one-sentence summary (under 20 words) explaining what this article is about.

Respond with ONLY a JSON object in this exact format, no other text:
{"category": "category name here", "summary": "one sentence summary here"}"""

    user_message = f"Title: {title}\nURL: {url}"

    try:
        response = get_client().messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=200,
            temperature=0,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )

        result_text = clean_json_response(response.content[0].text)
        result = json.loads(result_text)

        if result.get("category") not in CATEGORIES:
            result["category"] = "Other"

        return result

    except json.JSONDecodeError:
        print(f"  [Warning] Failed to parse JSON for: {title}")
        return {"category": "Other", "summary": "Unable to generate summary"}

    except Exception as e:
        print(f"  [Error] API call failed for: {title}")
        print(f"  Error: {e}")
        return {"category": "Other", "summary": "Unable to generate summary"}


# ============================================================
# 批量处理
# ============================================================
def categorize_stories(stories):
    total = len(stories)
    print(f"Categorizing {total} articles with Claude API...")

    for i, story in enumerate(stories):
        result = categorize_article(story["title"], story["url"])
        story["category"] = result["category"]
        story["summary"] = result["summary"]
        print(f"  [{i+1}/{total}] {story['category']}: {story['title'][:50]}...")

    print(f"\nDone! Categorized {total} articles.\n")
    return stories


# ============================================================
# 给书签文章生成详细分析
# ============================================================
def summarize_bookmark(title, content):
    system_prompt = """You are a tech content analyzer. Given an article title and its content, provide:
1. A 2-3 sentence summary of the key points
2. 3-5 relevant tags (comma-separated, lowercase)
3. A difficulty rating: beginner, intermediate, or advanced

Respond with ONLY a JSON object:
{"summary": "...", "tags": "tag1,tag2,tag3", "difficulty": "beginner|intermediate|advanced"}"""

    user_message = f"Title: {title}\n\nContent:\n{content[:3000]}"

    try:
        response = get_client().messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            temperature=0,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )

        result_text = clean_json_response(response.content[0].text)
        result = json.loads(result_text)

        return {
            "summary": result.get("summary", "No summary available"),
            "tags": result.get("tags", "untagged"),
            "difficulty": result.get("difficulty", "intermediate"),
        }

    except Exception as e:
        print(f"  [Error] Bookmark analysis failed: {e}")
        return {
            "summary": "Unable to generate summary",
            "tags": "untagged",
            "difficulty": "intermediate",
        }


if __name__ == "__main__":
    test_articles = [
        {"title": "GPT-5 achieves human-level reasoning on math benchmarks", "url": "https://example.com/1"},
        {"title": "Why Rust is replacing C++ in production systems", "url": "https://example.com/2"},
    ]

    print("Testing article categorization...")
    for article in test_articles:
        result = categorize_article(article["title"], article["url"])
        print(f"  {result['category']}: {result['summary']}")
    print("\n✅ API is working!")
