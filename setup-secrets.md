# GitHub Secrets 配置指南

为了让GitHub Actions能够正常运行FOMO新闻分析系统，你需要在GitHub仓库中配置以下Secrets。

## 配置步骤

1. 进入你的GitHub仓库页面
2. 点击 `Settings`（设置）
3. 在左侧菜单中找到 `Secrets and variables` > `Actions`
4. 点击 `New repository secret` 按钮
5. 依次添加以下Secrets

## 需要配置的Secrets

### 1. SUPABASE_URL
- **说明**: Supabase项目的URL
- **获取方式**: 
  1. 登录[Supabase控制台](https://app.supabase.com)
  2. 选择你的项目
  3. 在项目设置中找到Project URL
- **示例**: `https://xxxxx.supabase.co`

### 2. SUPABASE_ANON_KEY
- **说明**: Supabase的匿名公钥
- **获取方式**:
  1. 在Supabase项目设置中
  2. 找到API Settings
  3. 复制anon public key
- **示例**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`

### 3. PINECONE_API_KEY
- **说明**: Pinecone的API密钥
- **获取方式**:
  1. 登录[Pinecone控制台](https://app.pinecone.io)
  2. 在API Keys页面生成或复制密钥
- **示例**: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`

### 4. PINECONE_INDEX_NAME
- **说明**: Pinecone索引名称
- **获取方式**:
  1. 在Pinecone控制台中查看你的索引列表
  2. 使用对应的索引名称
- **示例**: `news-embeddings`

### 5. GOOGLE_API_KEY
- **说明**: Google Gemini API密钥
- **获取方式**:
  1. 访问[Google AI Studio](https://makersuite.google.com/app/apikey)
  2. 创建或获取API密钥
- **示例**: `AIzaSyxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

## 验证配置

配置完成后，你可以：

1. 手动触发工作流来测试配置是否正确
2. 在Actions页面点击 `Run workflow`
3. 查看运行日志确认没有认证错误

## 安全提醒

- 🔒 **永远不要**将这些密钥直接提交到代码仓库中
- 🔒 定期轮换密钥以保证安全
- 🔒 限制密钥的权限范围到最小必需
- 🔒 监控API使用情况，防止异常调用

## 故障排查

如果遇到认证问题：

1. **检查Secret名称**: 确保名称完全匹配（区分大小写）
2. **检查Secret值**: 确保没有多余的空格或换行
3. **检查API限额**: 确保API没有超出使用限额
4. **查看错误日志**: 在GitHub Actions的运行日志中查看具体错误信息