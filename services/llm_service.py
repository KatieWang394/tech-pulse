"""
llm_service.py — 用 Claude API 对文章进行分类和摘要

这个文件是整个项目的 "AI 大脑"：
- 给 HN 文章自动分类（AI, Web Dev, Security 等）
- 给 HN 文章生成一句话摘要
- 给书签文章生成详细摘要 + 标签（Day 3 会用到）

核心概念：
- 我们用的是 Anthropic 的 Claude API（就是你现在在对话的这个 AI）
- 调用方式和你之前用过的 API 类似：发一个请求，拿到一个响应
- 关键技巧在于 "prompt"（提示词）怎么写，这直接决定返回结果的质量
"""

import os
import json
from anthropic import Anthropic
from dotenv import load_dotenv

# load_dotenv() 会读取项目根目录下的 .env 文件，
# 把里面的 ANTHROPIC_API_KEY=xxx 加载到环境变量里
# 这样代码里就不用写死 API key 了（安全！）
load_dotenv()

# 初始化 Anthropic 客户端
# 它会自动从环境变量里读取 ANTHROPIC_API_KEY
client = Anthropic()

# ============================================================
# 分类列表 — 你可以根据自己的兴趣调整这些类别
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

# ============================================================
# 给 HN 文章分类 + 生成摘要
# ============================================================
def categorize_article(title, url):
    """
    发送文章标题和 URL 给 Claude，让它：
    1. 从预设类别中选一个最合适的
    2. 写一句话摘要

    参数:
        title: 文章标题（字符串）
        url:   文章链接（字符串）

    返回:
        一个字典：{"category": "AI / Machine Learning", "summary": "..."}
        如果 API 调用失败，返回默认值
    """

    # ---- Prompt 设计 ----
    # 这是整个文件最重要的部分。几个要点：
    # 1. system prompt 告诉 Claude 它的角色和输出格式
    # 2. 明确要求返回 JSON，这样我们可以直接 parse
    # 3. 给出具体的类别列表，避免 Claude 自己编类别
    # 4. 要求摘要简短（一句话），避免长篇大论浪费 token（= 浪费钱）

    system_prompt = """You are a tech news classifier. Given an article title and URL, you must:
1. Classify it into exactly ONE of these categories: """ + ", ".join(CATEGORIES) + """
2. Write a one-sentence summary (under 20 words) explaining what this article is about.

Respond with ONLY a JSON object in this exact format, no other text:
{"category": "category name here", "summary": "one sentence summary here"}"""

    user_message = f"Title: {title}\nURL: {url}"

    try:
        # ---- API 调用 ----
        # model: claude-haiku 最便宜最快，用来做分类这种简单任务完全够用
        # max_tokens: 限制返回长度，分类+摘要用不了多少 token
        # temperature: 0 表示让 Claude 尽量确定性地回答（不要太有创意）
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=200,
            temperature=0,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_message}
            ],
        )

        # 从响应中提取文本
        result_text = response.content[0].text.strip()
        # 去掉 Claude 有时候会加的 ```json ``` 包裹
        result_text = result_text.replace("```json", "").replace("```", "").strip()

        # 尝试解析 JSON
        result = json.loads(result_text)

        # 验证返回的类别是否在我们的列表里
        if result.get("category") not in CATEGORIES:
            result["category"] = "Other"

        return result

    except json.JSONDecodeError:
        # Claude 偶尔可能返回不完美的 JSON，这里兜底
        print(f"  [Warning] Failed to parse JSON for: {title}")
        print(f"  Raw response: {result_text}")
        return {"category": "Other", "summary": "Unable to generate summary"}

    except Exception as e:
        # 网络错误、API key 无效等等
        print(f"  [Error] API call failed for: {title}")
        print(f"  Error: {e}")
        return {"category": "Other", "summary": "Unable to generate summary"}


# ============================================================
# 批量处理：给一组文章都加上分类和摘要
# ============================================================
def categorize_stories(stories):
    """
    给一组 HN 文章批量添加 AI 分类和摘要。

    参数:
        stories: hn_fetcher.fetch_top_stories() 返回的文章列表

    返回:
        同样的列表，但每个文章字典多了 "category" 和 "summary" 两个字段

    注意：
        这个函数会调用很多次 API（每篇文章一次），所以：
        - 30 篇文章大概需要 30-60 秒
        - 费用大概 $0.01-0.02（用 Haiku 模型非常便宜）
    """
    total = len(stories)
    print(f"Categorizing {total} articles with Claude API...")

    for i, story in enumerate(stories):
        result = categorize_article(story["title"], story["url"])

        # 把 AI 的分析结果加到原来的字典里
        story["category"] = result["category"]
        story["summary"] = result["summary"]

        # 打印进度
        print(f"  [{i+1}/{total}] {story['category']}: {story['title'][:50]}...")

    print(f"\nDone! Categorized {total} articles.\n")
    return stories


# ============================================================
# 给书签文章生成详细分析（Day 3 的书签功能会用到）
# ============================================================
def summarize_bookmark(title, content):
    """
    给用户保存的书签文章生成详细摘要、标签和难度评级。

    参数:
        title:   文章标题
        content: 文章正文（前 2000 字左右）

    返回:
        字典：{"summary": "...", "tags": "tag1,tag2,tag3", "difficulty": "beginner"}
    """
    system_prompt = """You are a tech content analyzer. Given an article title and its content, provide:
1. A 2-3 sentence summary of the key points
2. 3-5 relevant tags (comma-separated, lowercase)
3. A difficulty rating: beginner, intermediate, or advanced

Respond with ONLY a JSON object:
{"summary": "...", "tags": "tag1,tag2,tag3", "difficulty": "beginner|intermediate|advanced"}"""

    user_message = f"Title: {title}\n\nContent:\n{content[:3000]}"

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            temperature=0,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_message}
            ],
        )

        result_text = response.content[0].text.strip()
        result_text = result_text.replace("```json", "").replace("```", "").strip()
        result = json.loads(result_text)

        # 确保所有字段都存在
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


# ============================================================
# 直接运行测试
# ============================================================
if __name__ == "__main__":
    # 测试分类功能：用几个假文章标题试试
    test_articles = [
        {"title": "GPT-5 achieves human-level reasoning on math benchmarks", "url": "https://example.com/1"},
        {"title": "Why Rust is replacing C++ in production systems", "url": "https://example.com/2"},
        {"title": "Show HN: I built a privacy-focused email client", "url": "https://example.com/3"},
        {"title": "YC-backed startup raises $50M for AI coding tools", "url": "https://example.com/4"},
    ]

    print("Testing article categorization...")
    print("=" * 60)

    for article in test_articles:
        result = categorize_article(article["title"], article["url"])
        print(f"\nTitle:    {article['title']}")
        print(f"Category: {result['category']}")
        print(f"Summary:  {result['summary']}")

    print("\n" + "=" * 60)
    print("If you see categories and summaries above, the API is working!")
    print("Cost for this test: ~$0.001 (less than a tenth of a cent)")
