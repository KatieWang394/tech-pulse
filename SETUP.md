# Tech Pulse — Day 1 Setup Guide

## 🚀 Quick Start (跟着做，5分钟跑起来)

### Step 1: 把项目文件夹放好
解压下载的 zip，放在你喜欢的位置，比如 `~/projects/tech-pulse/`

### Step 2: 打开终端，进入项目文件夹
```bash
cd ~/projects/tech-pulse
```

### Step 3: 创建虚拟环境（推荐但可选）
```bash
# 创建虚拟环境 — 把这个项目的依赖和你电脑上其他 Python 项目隔离开
python3 -m venv venv

# 激活虚拟环境
# Mac/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 激活后你的终端提示符前面会出现 (venv)，说明成功了
```

### Step 4: 安装依赖
```bash
pip install -r requirements.txt
```

### Step 5: 先测试 HN 数据获取
```bash
# 直接运行 fetcher 脚本，看看能不能拿到数据
python services/hn_fetcher.py
```
你应该能看到终端打印出 30 条 Hacker News 热门文章的标题、链接和分数。
如果看到了，说明数据获取这一层完全没问题！

### Step 6: 启动 Streamlit 看效果
```bash
streamlit run app.py
```
浏览器会自动打开 `http://localhost:8501`，你会看到 Tech Pulse 的界面。
点 "Fetch Latest from Hacker News" 按钮，文章就会出现。

---

## 📁 当前项目结构
```
tech-pulse/
├── app.py                  ← 主页面（Streamlit 入口）
├── services/
│   ├── __init__.py         ← 让 Python 识别这是一个包
│   └── hn_fetcher.py       ← HN API 数据获取（Day 1 核心）
├── pages/                  ← Day 4-5 会在这里加页面
├── requirements.txt        ← Python 依赖列表
├── .env.example            ← API key 模板（Day 2 用）
├── .gitignore              ← Git 忽略规则
└── SETUP.md                ← 你正在看的这个文件
```

## ✅ Day 1 Checklist
- [ ] `python services/hn_fetcher.py` 能打印出文章列表
- [ ] `streamlit run app.py` 能在浏览器里看到界面
- [ ] 点按钮能加载文章
- [ ] 在 GitHub 上创建 repo，push 第一个 commit

## 📝 Git 初始化 (如果还没建 repo)
```bash
git init
git add .
git commit -m "Day 1: project setup + HN fetcher"

# 然后去 GitHub 创建一个新 repo (名字就叫 tech-pulse)
# 按照 GitHub 页面上的提示连接远程仓库:
git remote add origin https://github.com/YOUR_USERNAME/tech-pulse.git
git branch -M main
git push -u origin main
```

## 🔜 Day 2 Preview
明天会加上 Claude API 来自动分类和总结文章。
你需要提前做一件事：去 https://console.anthropic.com/ 注册账号，
拿到 API key，复制 `.env.example` 为 `.env`，把 key 填进去。
