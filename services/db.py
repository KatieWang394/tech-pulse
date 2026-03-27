"""
db.py — 数据库操作（SQLite）

这个文件负责所有跟数据库打交道的事情：
- 创建表（如果不存在的话）
- 存文章、存书签
- 查询文章、查询书签
- 获取趋势统计数据

为什么用 SQLite？
- Python 自带，不用额外安装任何东西
- 数据存在一个 .db 文件里，不需要运行数据库服务器
- 你已经会 SQL，所以上手零成本
- 对于个人项目完全够用

关键概念：
- connection: 跟数据库的连接，类似于"打开文件"
- cursor: 用来执行 SQL 语句的工具，类似于"文件指针"
- commit: 确认保存修改，类似于 Ctrl+S
"""

import sqlite3
import os
from datetime import datetime, timedelta

# 数据库文件路径 — 会自动创建在项目根目录下
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tech_pulse.db")


def get_connection():
    """
    获取数据库连接。

    row_factory = sqlite3.Row 这行很有用：
    它让查询结果可以用列名访问（result["title"]），
    而不是只能用索引（result[1]），可读性好很多。
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """
    初始化数据库：创建需要的表（如果还不存在的话）。

    IF NOT EXISTS 的意思是：表已经存在就跳过，不存在才创建。
    所以这个函数可以安全地多次调用，不会覆盖已有数据。
    """
    conn = get_connection()
    cursor = conn.cursor()

    # ---- 表 1: hn_articles ----
    # 存储从 Hacker News 抓取的文章及其 AI 分析结果
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hn_articles (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            hn_id       INTEGER UNIQUE,
            title       TEXT NOT NULL,
            url         TEXT,
            score       INTEGER DEFAULT 0,
            author      TEXT,
            category    TEXT,
            summary     TEXT,
            fetched_at  DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ---- 表 2: bookmarks ----
    # 存储用户手动保存的文章及其 AI 生成的摘要和标签
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookmarks (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            url             TEXT UNIQUE,
            title           TEXT,
            content_snippet TEXT,
            summary         TEXT,
            tags            TEXT,
            difficulty      TEXT DEFAULT 'intermediate',
            user_notes      TEXT,
            saved_at        DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_PATH}")


# ============================================================
# HN 文章相关操作
# ============================================================

def save_articles(stories):
    """
    批量保存 HN 文章到数据库。

    INSERT OR IGNORE 的意思是：如果 hn_id 已经存在（UNIQUE 约束），
    就跳过这条记录。这样重复抓取同一篇文章不会报错也不会覆盖。

    参数:
        stories: categorize_stories() 返回的文章列表

    返回:
        (new_count, skip_count) 新增了多少篇，跳过了多少篇
    """
    conn = get_connection()
    cursor = conn.cursor()

    new_count = 0
    skip_count = 0

    for story in stories:
        cursor.execute("""
            INSERT OR IGNORE INTO hn_articles 
                (hn_id, title, url, score, author, category, summary)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            story["hn_id"],
            story["title"],
            story["url"],
            story["score"],
            story["author"],
            story.get("category", "Other"),
            story.get("summary", ""),
        ))

        # rowcount 告诉你这次 INSERT 是否真的插入了一行
        # 1 = 插入成功，0 = 被 IGNORE 了（说明已经存在）
        if cursor.rowcount > 0:
            new_count += 1
        else:
            skip_count += 1

    conn.commit()
    conn.close()
    return new_count, skip_count


def get_recent_articles(days=7, category=None):
    """
    查询最近 N 天的文章。

    参数:
        days:     查最近几天的，默认 7 天
        category: 可选，按类别筛选

    返回:
        文章列表（每个元素是 sqlite3.Row 对象，可以用列名访问）
    """
    conn = get_connection()
    cursor = conn.cursor()

    since = datetime.now() - timedelta(days=days)

    if category and category != "All":
        cursor.execute("""
            SELECT * FROM hn_articles
            WHERE fetched_at >= ? AND category = ?
            ORDER BY fetched_at DESC, score DESC
        """, (since.isoformat(), category))
    else:
        cursor.execute("""
            SELECT * FROM hn_articles
            WHERE fetched_at >= ?
            ORDER BY fetched_at DESC, score DESC
        """, (since.isoformat(),))

    articles = cursor.fetchall()
    conn.close()
    return articles


def get_category_counts(days=7):
    """
    统计最近 N 天各类别的文章数量。
    用于趋势看板的柱状图。

    返回:
        字典，例如 {"AI / Machine Learning": 8, "Web Development": 5, ...}
    """
    conn = get_connection()
    cursor = conn.cursor()

    since = datetime.now() - timedelta(days=days)

    cursor.execute("""
        SELECT category, COUNT(*) as count
        FROM hn_articles
        WHERE fetched_at >= ?
        GROUP BY category
        ORDER BY count DESC
    """, (since.isoformat(),))

    result = {row["category"]: row["count"] for row in cursor.fetchall()}
    conn.close()
    return result


def get_daily_trend(days=7):
    """
    按天统计各类别文章数量，用于趋势折线图。

    返回:
        列表，例如:
        [{"date": "2026-03-20", "AI / Machine Learning": 3, "Web Development": 2}, ...]
    """
    conn = get_connection()
    cursor = conn.cursor()

    since = datetime.now() - timedelta(days=days)

    cursor.execute("""
        SELECT DATE(fetched_at) as date, category, COUNT(*) as count
        FROM hn_articles
        WHERE fetched_at >= ?
        GROUP BY DATE(fetched_at), category
        ORDER BY date
    """, (since.isoformat(),))

    # 把查询结果转换成 Streamlit 图表需要的格式
    trend = {}
    for row in cursor.fetchall():
        date = row["date"]
        if date not in trend:
            trend[date] = {"date": date}
        trend[date][row["category"]] = row["count"]

    conn.close()
    return list(trend.values())


# ============================================================
# 书签相关操作
# ============================================================

def save_bookmark(url, title, content_snippet, summary, tags, difficulty, user_notes=""):
    """
    保存一个书签到数据库。

    INSERT OR REPLACE 的意思是：如果 URL 已经存在，就更新那条记录。
    这样用户可以重新分析同一个 URL 并更新结果。

    返回:
        True 表示保存成功，False 表示失败
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT OR REPLACE INTO bookmarks
                (url, title, content_snippet, summary, tags, difficulty, user_notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (url, title, content_snippet, summary, tags, difficulty, user_notes))

        conn.commit()
        return True
    except Exception as e:
        print(f"Error saving bookmark: {e}")
        return False
    finally:
        conn.close()


def get_bookmarks(search_query=None, tag_filter=None):
    """
    查询书签列表，支持关键词搜索和标签筛选。

    参数:
        search_query: 搜索关键词（在标题和摘要中搜索）
        tag_filter:   按标签筛选

    返回:
        书签列表
    """
    conn = get_connection()
    cursor = conn.cursor()

    if search_query:
        # LIKE '%xxx%' 是 SQL 的模糊搜索，% 表示任意字符
        query = f"%{search_query}%"
        cursor.execute("""
            SELECT * FROM bookmarks
            WHERE title LIKE ? OR summary LIKE ? OR tags LIKE ?
            ORDER BY saved_at DESC
        """, (query, query, query))
    elif tag_filter:
        cursor.execute("""
            SELECT * FROM bookmarks
            WHERE tags LIKE ?
            ORDER BY saved_at DESC
        """, (f"%{tag_filter}%",))
    else:
        cursor.execute("SELECT * FROM bookmarks ORDER BY saved_at DESC")

    bookmarks = cursor.fetchall()
    conn.close()
    return bookmarks


def get_all_tags():
    """
    获取所有书签中出现过的标签（去重）。
    用于前端的标签筛选下拉菜单。

    返回:
        排序后的标签列表，例如 ["ai", "python", "security", "web"]
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT tags FROM bookmarks WHERE tags IS NOT NULL")

    all_tags = set()
    for row in cursor.fetchall():
        # tags 字段存的是逗号分隔的字符串，比如 "ai,python,web"
        for tag in row["tags"].split(","):
            tag = tag.strip().lower()
            if tag and tag != "untagged":
                all_tags.add(tag)

    conn.close()
    return sorted(all_tags)


def delete_bookmark(bookmark_id):
    """删除一个书签。"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM bookmarks WHERE id = ?", (bookmark_id,))
    conn.commit()
    conn.close()


# ============================================================
# 直接运行测试
# ============================================================
if __name__ == "__main__":
    print("Initializing database...")
    init_db()

    # 测试插入一些假数据
    test_stories = [
        {
            "hn_id": 99999001,
            "title": "Test Article: AI is Amazing",
            "url": "https://example.com/test1",
            "score": 100,
            "author": "testuser",
            "category": "AI / Machine Learning",
            "summary": "A test article about AI.",
        },
        {
            "hn_id": 99999002,
            "title": "Test Article: New JS Framework",
            "url": "https://example.com/test2",
            "score": 50,
            "author": "testuser",
            "category": "Web Development",
            "summary": "Yet another JavaScript framework.",
        },
    ]

    new, skipped = save_articles(test_stories)
    print(f"Saved {new} new articles, skipped {skipped}")

    # 测试查询
    articles = get_recent_articles(days=1)
    print(f"\nRecent articles: {len(articles)}")
    for a in articles:
        print(f"  [{a['category']}] {a['title']}")

    # 测试类别统计
    counts = get_category_counts(days=1)
    print(f"\nCategory counts: {counts}")

    # 测试书签
    save_bookmark(
        url="https://example.com/bookmark-test",
        title="Test Bookmark",
        content_snippet="This is test content...",
        summary="A test bookmark for database testing.",
        tags="test,database,python",
        difficulty="beginner",
    )

    bookmarks = get_bookmarks()
    print(f"\nBookmarks: {len(bookmarks)}")
    for b in bookmarks:
        print(f"  [{b['difficulty']}] {b['title']} — tags: {b['tags']}")

    print("\nAll tags:", get_all_tags())
    print("\n✅ Database tests passed!")
