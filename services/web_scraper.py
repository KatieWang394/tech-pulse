"""
web_scraper.py — 从网页 URL 提取文章内容

当用户想保存一个书签时，这个文件负责：
1. 用 requests 下载网页的 HTML
2. 用 BeautifulSoup 从 HTML 中提取标题和正文
3. 清理掉导航栏、广告、页脚等无关内容

为什么需要这个？
- 用户只需要粘贴一个 URL
- 我们自动帮他获取文章内容
- 然后把内容发给 Claude API 做摘要和打标签

BeautifulSoup 是什么？
- 一个 Python 库，专门用来解析 HTML
- 你可以用它像查字典一样查找 HTML 里的元素
- 名字来自《爱丽丝梦游仙境》里的一首诗（没什么特别含义）
"""

import requests
from bs4 import BeautifulSoup


def fetch_article_content(url):
    """
    从 URL 获取文章的标题和正文内容。

    参数:
        url: 文章的完整 URL

    返回:
        字典：{"title": "文章标题", "content": "文章正文前2000字"}
        如果获取失败，返回带有错误信息的字典
    """

    try:
        # ---- 第一步：下载网页 ----
        # headers 里设置 User-Agent 是因为有些网站会拒绝
        # 看起来像机器人的请求。设置一个常见的浏览器 UA 就行。
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }

        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        # 有些网页的编码不是 UTF-8，response.text 会自动处理
        html = response.text

        # ---- 第二步：解析 HTML ----
        # "html.parser" 是 Python 自带的解析器，不需要额外安装
        soup = BeautifulSoup(html, "html.parser")

        # ---- 第三步：提取标题 ----
        title = extract_title(soup)

        # ---- 第四步：提取正文 ----
        content = extract_content(soup)

        if not content or len(content.strip()) < 50:
            return {
                "title": title or "Unknown Title",
                "content": "Could not extract meaningful content from this page.",
                "success": False,
            }

        return {
            "title": title or "Unknown Title",
            "content": content[:3000],  # 限制长度，节省 API token
            "success": True,
        }

    except requests.Timeout:
        return {
            "title": "Error",
            "content": "Request timed out. The website took too long to respond.",
            "success": False,
        }
    except requests.RequestException as e:
        return {
            "title": "Error",
            "content": f"Failed to fetch the URL: {str(e)}",
            "success": False,
        }


def extract_title(soup):
    """
    从 HTML 中提取文章标题。

    尝试多种方法，因为不同网站的标题位置不一样：
    1. <meta property="og:title"> — 社交分享标题，通常最准确
    2. <h1> 标签 — 文章主标题
    3. <title> 标签 — 网页标题（可能包含网站名）
    """
    # 方法 1: Open Graph 标题
    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        return og_title["content"].strip()

    # 方法 2: 第一个 h1
    h1 = soup.find("h1")
    if h1 and h1.get_text(strip=True):
        return h1.get_text(strip=True)

    # 方法 3: title 标签
    if soup.title and soup.title.string:
        return soup.title.string.strip()

    return None


def extract_content(soup):
    """
    从 HTML 中提取文章正文。

    这是最 tricky 的部分——每个网站的 HTML 结构都不同。
    我们的策略是：
    1. 先删掉明显不是正文的元素（导航栏、脚本、广告等）
    2. 尝试找 <article> 标签（很多博客和新闻网站用这个包裹正文）
    3. 如果没有 <article>，就找 <main>
    4. 如果都没有，就收集所有 <p> 标签的文本

    这个方法不完美（没有任何方法是完美的），但对大部分技术博客和新闻网站够用。
    """

    # 删掉不需要的元素 — 这些几乎不可能是正文
    for tag_name in ["script", "style", "nav", "footer", "header", "aside", "iframe"]:
        for tag in soup.find_all(tag_name):
            tag.decompose()  # decompose = 从 HTML 树中彻底删除

    # 同样删掉常见的非正文 class/id
    for selector in [
        "[class*='sidebar']", "[class*='comment']", "[class*='footer']",
        "[class*='nav']", "[class*='menu']", "[class*='ad-']",
        "[id*='sidebar']", "[id*='comment']", "[id*='footer']",
    ]:
        for tag in soup.select(selector):
            tag.decompose()

    # 策略 1: 找 <article> 标签
    article = soup.find("article")
    if article:
        return clean_text(article)

    # 策略 2: 找 <main> 标签
    main = soup.find("main")
    if main:
        return clean_text(main)

    # 策略 3: 找所有 <p> 标签，拼起来
    paragraphs = soup.find_all("p")
    if paragraphs:
        texts = []
        for p in paragraphs:
            text = p.get_text(strip=True)
            # 只保留有实质内容的段落（超过 30 个字符）
            if len(text) > 30:
                texts.append(text)
        return "\n\n".join(texts)

    # 实在找不到就返回空
    return ""


def clean_text(element):
    """
    从一个 HTML 元素中提取干净的文本。
    get_text() 会拿到所有子元素的文本，
    separator="\n" 让每个块级元素之间换行。
    """
    text = element.get_text(separator="\n", strip=True)

    # 把连续多个换行合并成两个（段落分隔）
    lines = text.split("\n")
    cleaned_lines = []
    for line in lines:
        line = line.strip()
        if line:
            cleaned_lines.append(line)

    return "\n\n".join(cleaned_lines)


# ============================================================
# 直接运行测试
# ============================================================
if __name__ == "__main__":
    # 用几个真实 URL 测试
    test_urls = [
        "https://www.paulgraham.com/writes.html",
        "https://github.com/anthropics/anthropic-sdk-python",
    ]

    for url in test_urls:
        print(f"\n{'=' * 60}")
        print(f"Fetching: {url}")
        print("=" * 60)

        result = fetch_article_content(url)
        print(f"Title:   {result['title']}")
        print(f"Success: {result['success']}")
        print(f"Content preview ({len(result['content'])} chars):")
        print(result["content"][:300] + "...")
