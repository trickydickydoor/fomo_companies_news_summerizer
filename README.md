# FOMO新闻摘要系统 - GitHub Actions 自动化版本

这是FOMO新闻摘要系统的GitHub Actions自动化版本，用于定时自动分析新闻并生成报告。

## 功能特性

- 🤖 自动化运行新闻分析（默认24小时，所有公司）
- ⏰ 支持定时触发（每12小时运行）
- 📊 智能分析：仅分析文章数量有变化的公司
- 📈 分析结果自动保存为Artifacts
- 🔔 支持结果通知（可选）
- 🔐 安全的Secrets管理
- 💾 自动保存分析结果到数据库

## 默认配置

- **分析时间范围**: 24小时
- **分析目标**: 所有公司（仅文章数量有变化的）
- **运行频率**: 每12小时自动运行
- **智能检测**: 基于current_article_count和last_article_count变化

## 配置说明

### 1. 设置GitHub Secrets

在你的仓库设置中添加以下Secrets：

- `SUPABASE_URL`: Supabase项目URL
- `SUPABASE_ANON_KEY`: Supabase匿名密钥
- `PINECONE_API_KEY`: Pinecone API密钥
- `PINECONE_INDEX_NAME`: Pinecone索引名称
- `GOOGLE_API_KEY`: Google Gemini API密钥

### 2. 运行配置

工作流支持以下触发方式：

- **定时触发**: 每12小时自动运行（UTC时间00:00和12:00）
- **手动触发**: 在Actions页面手动运行，可覆盖默认参数
- **Push触发**: 推送到main分支时自动运行

### 3. 智能分析机制

系统现在具备智能分析功能：

- **文章计数检测**: 系统会比较每个公司的 `current_article_count` 和 `last_article_count`
- **选择性分析**: 只有文章数量发生变化的公司才会被分析
- **自动更新**: 分析完成后，自动将 `last_article_count` 更新为开始分析时的 `current_article_count`
- **效率提升**: 避免重复分析相同数据，显著提高系统效率

### 4. 自定义参数（可选）

手动运行时可以覆盖默认值：

- `hours`: 分析时间范围（默认24小时）
- `company`: 特定公司名称（默认为空，分析所有公司）
- `save_to_db`: 是否保存到数据库（默认true）

## 文件结构

```
github-action/
├── .github/
│   └── workflows/
│       └── news-analysis.yml    # GitHub Actions工作流配置
├── run_analysis.py             # 自动化运行脚本
├── requirements.txt            # Python依赖
└── README.md                  # 本文件
```

## 使用方法

1. Fork或复制此项目到你的GitHub仓库
2. 配置必要的GitHub Secrets
3. 根据需要修改定时触发时间（可选）
4. 推送代码，自动化任务将按计划运行

## 查看结果

- 分析结果将保存为GitHub Artifacts，可在Actions运行历史中下载
- 结果文件命名格式：`news-analysis-YYYY-MM-DD-HH-mm.json`
- 日志文件：`analysis-log-YYYY-MM-DD-HH-mm.txt`

## 修改定时运行时间

编辑 `.github/workflows/news-analysis.yml` 文件中的cron表达式：

```yaml
schedule:
  - cron: '0 */12 * * *'  # UTC时间，每12小时运行一次（00:00和12:00）
```

Cron表达式说明：
- 分钟 小时 日 月 星期
- 当前配置：`0 */12 * * *` 表示每12小时运行一次
- 其他示例：
  - `0 */6 * * *` 表示每6小时运行一次
  - `0 0,8,16 * * *` 表示每天UTC时间0:00、8:00、16:00运行

## 智能分析工作流程

1. **获取公司列表**: 从Supabase获取所有公司信息
2. **检查文章计数**: 比较每个公司的current_article_count和last_article_count
3. **选择性分析**: 只对文章数量有变化的公司进行分析
4. **执行分析**: 使用Pinecone和Gemini进行新闻分析
5. **更新计数**: 分析完成后更新last_article_count
6. **生成报告**: 保存分析结果和统计信息

## 效率优化

- **智能跳过**: 文章数量无变化的公司将被跳过，节省计算资源
- **批量处理**: 同时处理多家公司的分析
- **结果缓存**: 避免重复分析相同内容
- **统计追踪**: 详细记录分析、跳过和成功的公司数量