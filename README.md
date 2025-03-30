# 新闻聚合与分析系统 - 你的智能信息管家 🤖📰

## 项目概述

在信息爆炸的时代，高效获取和理解新闻资讯至关重要。这款基于 Python 和 PyQt5 的新闻聚合与分析系统，旨在成为您的智能信息助手，帮助您：

*   **聚合信息:** 自动从您指定的 RSS 源和澎湃新闻等渠道收集最新内容。
*   **智能整理:** 对获取的新闻进行自动分类，使信息结构化。
*   **AI 赋能:** 利用大语言模型（LLM）快速生成新闻摘要、进行情感分析、提取关键观点，并能通过聊天界面与 AI 探讨新闻内容。
*   **便捷管理:** 提供新闻源管理、浏览历史回顾、数据导入导出等实用功能。

本项目致力于提供一个便捷、智能的新闻处理平台。

## 主要功能

1.  **新闻采集:**
    *   **RSS 源:** 灵活添加和管理 RSS 订阅。
    *   **澎湃新闻:** 内置对澎湃新闻的支持。
    *   **自动分类:** 基于新闻来源进行初步分类。

2.  **新闻分析 (LLM):**
    *   **智能摘要:** 快速了解文章核心内容。
    *   **深度分析:** 获取对新闻事件更深层次的解读。
    *   **关键观点:** 提取文章的主要论点。
    *   **事实核查 (概念性):** 探索性功能，旨在辅助信息辨别。
    *   **智能聊天:** 与 AI 进行基于新闻或开放主题的对话。

3.  **用户界面:**
    *   **新闻列表:** 清晰展示新闻条目，标记已读状态。
    *   **分类导航:** 通过侧边栏快速筛选不同类别的新闻。
    *   **内容搜索:** 支持按关键词搜索标题和/或内容。
    *   **详情阅读:** 双击可在独立窗口阅读新闻，支持字体缩放和内容复制。
    *   **个性化:** 提供日间/夜间主题切换和全局字体大小调整功能。

## 技术栈

*   **Python 3.10+:** 项目核心语言。
*   **PyQt5:** 构建图形用户界面。
*   **Requests / Feedparser:** 用于网络请求和 RSS 解析。
*   **BeautifulSoup4:** HTML 内容解析。
*   **python-dateutil:** 日期时间格式处理。
*   **Transformers / LLM Client:** 大语言模型集成接口。
*   **QSettings:** 应用程序设置存储。

## 安装指南

1.  **克隆仓库:**
    ```bash
    git clone https://github.com/your-repo/news_analyzer.git # 请替换为实际仓库地址
    cd news_analyzer
    ```

2.  **安装依赖:**
    ```bash
    pip install -r requirements.txt
    # 如果遇到网络问题，可以尝试使用国内镜像源:
    # pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    ```
    * **注意:** LLM 功能可能需要额外的库 (例如 `openai`)，请根据您选择的模型服务商进行安装。

3.  **运行程序:**
    ```bash
    python main.py
    ```

## 文件结构

```
news_analyzer/
├── collectors/      # 新闻采集器模块
├── config/          # 配置文件和管理（比如 LLM 设置）
├── core/            # 核心业务逻辑，协调各个模块
├── data/            # 存放用户数据、缓存等
├── llm/             # 大语言模型客户端和相关逻辑
├── models/          # 定义数据结构（如 NewsSource, NewsArticle）
├── storage/         # 数据持久化存储管理
├── ui/              # 用户界面组件
└── logs/            # 日志文件目录
main.py              # 程序主入口
README.md            # 项目说明文件
requirements.txt     # Python 依赖列表
... 其他配置文件或脚本 ...
```

## 注意事项

1.  **LLM API 密钥:** 使用 AI 相关功能前，请务必在“设置”菜单中配置您的大语言模型 API 密钥及相关参数。本项目不提供 API Key。
2.  **首次运行:** 程序首次运行时会在 `data` 目录下自动创建所需文件。
3.  **日志:** `logs` 目录包含运行日志，有助于排查问题。日志文件会增长，可定期清理。
4.  **网络连接:** 新闻源刷新和 LLM 功能需要正常的网络连接。
5.  **开发状态:** 本项目仍在开发和完善中，欢迎提出宝贵的意见和建议。

## 支持项目？☕️

如果您觉得这个项目对您有帮助，节省了您的时间或带来了便利，可以考虑请我喝杯咖啡，支持项目的持续开发和维护。

每一份支持都是项目前进的动力，非常感谢！

| 支付宝 (Alipay) | 微信支付 (WeChat Pay) |
| :-------------: | :-----------------: |
| ![支付宝收款码](images/alipay_qr.png) | ![微信支付收款码](images/wechat_qr.png) |
| (推荐使用支付宝) | (推荐使用微信支付) |

---

感谢您的使用与支持！
