"""
hn_fetcher.py — 从 Hacker News API 获取热门文章

Hacker News API 是完全免费的，不需要 API key，不需要注册。
文档：https://github.com/HackerNewsAPI/HackerNews-API

工作原理：
1. 先调用 /topstories 拿到当前热门文章的 ID 列表（一堆数字）
2. 再逐个调用 /item/{id} 拿到每篇文章的详细信息（标题、链接、分数等）
"""

import requests
import time


# ============================================================
# Hacker News API 的基础地址，所有请求都从这里开始
# ============================================================
HN_BASE_URL = "https://hacker-news.firebaseio.com/v0"


def fetch_top_story_ids(limit=30):
    """
    获取当前 HN 首页热门文章的 ID 列表。

    参数:
        limit: 要获取多少篇，默认 30（HN 首页大概就是 30 条）

    返回:
        一个整数列表，比如 [41893243, 41892771, ...]
    """
    url = f"{HN_BASE_URL}/topstories.json"

    # requests.get() 就是发一个 HTTP GET 请求，和你在浏览器里输入网址是一样的
    response = requests.get(url, timeout=10)

    # raise_for_status() 的意思是：如果请求失败了（比如 404），就抛出一个错误
    # 而不是默默地继续运行。这是一个好习惯。
    response.raise_for_status()

    # .json() 把返回的 JSON 字符串变成 Python 对象（这里是一个列表）
    all_ids = response.json()

    # 只取前 limit 个
    return all_ids[:limit]


def fetch_story_detail(story_id):
    """
    根据文章 ID 获取这篇文章的详细信息。

    参数:
        story_id: 文章的数字 ID

    返回:
        一个字典，包含文章的标题、链接、分数等信息。
        如果获取失败，返回 None。
    """
    url = f"{HN_BASE_URL}/item/{story_id}.json"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        # 有些 HN 帖子没有外部链接（比如 Ask HN 帖子），
        # 这种情况下我们就用 HN 自己的讨论页链接
        if data is None:
            return None

        return {
            "hn_id": data.get("id"),
            "title": data.get("title", "No title"),
            "url": data.get("url", f"https://news.ycombinator.com/item?id={story_id}"),
            "score": data.get("score", 0),
            "author": data.get("by", "unknown"),
            "time": data.get("time", 0),  # Unix timestamp
            "num_comments": data.get("descendants", 0),
        }

    except requests.RequestException as e:
        # 如果某一篇文章获取失败，打印一下错误，跳过这篇，继续处理其他的
        print(f"  [Warning] Failed to fetch story {story_id}: {e}")
        return None


def fetch_top_stories(limit=30):
    """
    主函数：获取 HN 热门文章列表，包含完整信息。

    这个函数把上面两个函数组合起来：
    1. 先拿到 ID 列表
    2. 再逐个获取详情
    3. 过滤掉获取失败的

    参数:
        limit: 获取多少篇

    返回:
        文章详情的列表，每个元素是一个字典
    """
    print(f"Fetching top {limit} stories from Hacker News...")

    # 第一步：拿到 ID 列表
    story_ids = fetch_top_story_ids(limit)
    print(f"Got {len(story_ids)} story IDs")

    # 第二步：逐个获取详情
    stories = []
    for i, story_id in enumerate(story_ids):
        detail = fetch_story_detail(story_id)
        if detail:
            stories.append(detail)

        # 每获取 10 篇打印一下进度，让你知道程序还在运行
        if (i + 1) % 10 == 0:
            print(f"  Fetched {i + 1}/{len(story_ids)} stories...")

        # 稍微等一下，避免请求太快（虽然 HN API 没有严格限制，但这是好习惯）
        time.sleep(0.05)

    print(f"Successfully fetched {len(stories)} stories\n")
    return stories


# ============================================================
# 下面这段代码只在你直接运行这个文件时执行
# 也就是说：python hn_fetcher.py 会执行这里
# 但如果其他文件 import hn_fetcher，不会执行这里
# 这是 Python 的标准模式，面试的时候可能会被问到
# ============================================================
if __name__ == "__main__":
    stories = fetch_top_stories(30)

    print("=" * 70)
    print(f"TOP {len(stories)} HACKER NEWS STORIES RIGHT NOW")
    print("=" * 70)

    for i, story in enumerate(stories, 1):
        print(f"\n#{i} [{story['score']} points] {story['title']}")
        print(f"   URL: {story['url'][:80]}{'...' if len(story['url']) > 80 else ''}")
        print(f"   By: {story['author']} | Comments: {story['num_comments']}")
