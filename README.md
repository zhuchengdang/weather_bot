
***

# 🌤️ Weather Bot - 自动天气提醒机器人

这是一个基于 Python 的轻量级天气提醒机器人。它通过高德地图 API 获取指定城市的实时天气数据，生成穿衣建议，并通过 **钉钉 (DingTalk)** 和 **电子邮件 (Email)** 发送通知。

该项目专为 **GitHub Actions** 设计，可定时自动运行（例如每天早上），为你推送当天的天气简报。

## ✨ 功能特性

*   **实时天气获取**：对接高德地图 API，获取温度、湿度、风向及天气状况。
*   **智能穿衣建议**：根据温度和天气现象（雨/雪/雾）自动生成人性化的穿衣和生活提示。
*   **多渠道通知**：
    *   📌 **钉钉群机器人**：支持 Markdown 格式消息，@所有人。
    *   📧 **电子邮件**：发送精美的 HTML格式邮件。
*   **GitHub Actions 集成**：无需服务器，利用 GitHub 免费算力定时执行。

## 🛠️ 前置准备

在配置 GitHub Actions 之前，你需要准备以下信息：

### 1. 高德地图 API Key
1.  访问 [高德开放平台](https://console.amap.com/dev/key/app)。
2.  注册/登录账号，创建新应用。
3.  添加 Key，服务平台选择 **Web服务**。
4.  复制生成的 `Key`。

### 2. 钉钉群机器人 Webhook
1.  在钉钉群聊中，点击群设置 -> **智能群助手** -> **添加机器人** -> **自定义**。
2.  安全设置建议选择 **加签**（推荐）或 **IP地址段**（GitHub Actions IP 不固定，建议用加签或关键词）。
    *   *注意：当前代码示例中暂未实现加签计算逻辑，若开启加签，需修改 [send_dingtalk](file:///home/danny/share/weather-bot/weather_bot.py#L60-L93) 函数以支持签名计算。若仅用于测试，可暂时关闭加签或使用关键词匹配（如消息中包含“天气”）。*
3.  复制 **Webhook 地址**。

### 3. 邮箱 SMTP 配置
你需要一个支持 SMTP 服务的邮箱账号（如 QQ邮箱、163邮箱、Gmail 等）。
*   **SMTP 服务器地址** (例如: `smtp.qq.com`)
*   **SMTP 端口** (SSL通常为 465, TLS通常为 587)
*   **发件人邮箱**
*   **授权码/密码** (注意：不是登录密码，需在邮箱设置中开启 SMTP 并获取授权码)
*   **收件人邮箱**

## ⚙️ GitHub Secrets 配置

为了安全起见，所有敏感信息都应存储在 GitHub Repository 的 **Secrets** 中，而不是直接写在代码里。

1.  进入你的 GitHub 仓库页面。
2.  点击 **Settings** -> **Secrets and variables** -> **Actions**。
3.  点击 **New repository secret**，依次添加以下变量：

| Secret Name | 描述 | 示例值 |
| :--- | :--- | :--- |
| `AMAP_API_KEY` | 高德地图 API Key | `a1b2c3d4e5...` |
| `DINGTALK_WEBHOOK` | 钉钉机器人 Webhook URL | `https://oapi.dingtalk.com/robot/send?access_token=...` |
| `DINGTALK_SECRET` | (可选) 钉钉加签密钥 | `SECxxxx...` |
| `EMAIL_SMTP_SERVER` | SMTP 服务器地址 | `smtp.qq.com` |
| `EMAIL_SMTP_PORT` | SMTP 端口 | `465` |
| `EMAIL_SENDER` | 发件人邮箱 | `bot@example.com` |
| `EMAIL_PASSWORD` | 邮箱授权码/密码 | `your_auth_code` |
| `EMAIL_RECEIVER` | 收件人邮箱 | `me@example.com` |

## 🚀 GitHub Actions 配置

在项目根目录下创建 `.github/workflows/weather.yml` 文件。

### 配置说明：
*   **触发时间 (`cron`)**：示例中设置为每天 UTC 00:00。你可以根据需要修改 cron 表达式。注意 GitHub Actions 使用 UTC 时间，北京时间需减去 8 小时。
    *   例如：想要北京时间早上 7:00 发送，应设置为 `0 23 * * *` (前一天的 23:00 UTC)。
*   **手动触发 (`workflow_dispatch`)**：添加了此选项后，你可以在 Actions 页面手动点击 "Run workflow" 来测试配置是否正确，无需等待定时任务。
*   **依赖安装**：脚本仅依赖 `requests` 库，标准库中的 `smtplib`, `email`, `json` 等无需额外安装。

## 📂 项目结构

```text
.
├── .github/
│   └── workflows/
│       └── weather.yml      # GitHub Actions 配置文件
├── weather_bot.py           # 主程序脚本
├── requirements.txt         # (可选) 依赖列表，目前仅需 requests
└── README.md                # 项目说明文档
```

## ⚠️ 注意事项

1.  **钉钉加签问题**：
    当前的 [send_dingtalk](file:///home/danny/share/weather-bot/weather_bot.py#L60-L93) 函数是一个基础实现。如果你在钉钉机器人设置中开启了 **加签 (Sign)** 安全设置，请求将会失败。
    *   **解决方案 A**：在钉钉机器人安全设置中关闭加签，改用 **关键词** 匹配（确保发送的消息中包含你设置的关键词，如“天气”）。
    *   **解决方案 B**：修改 [weather_bot.py](file:///home/danny/share/weather-bot/weather_bot.py) 中的 [send_dingtalk](file:///home/danny/share/weather-bot/weather_bot.py#L60-L93) 函数，增加 HMAC-SHA256 签名计算逻辑。

2.  **邮箱安全性**：
    建议使用专门的小号邮箱或开启 SMTP 授权码的服务，不要直接使用主邮箱的登录密码。

3.  **API 配额**：
    高德地图个人开发者有一定的每日调用次数限制，请留意配额使用情况。对于每日一次的频率，完全足够。

## 📝 自定义城市

如果需要修改监控的城市，请编辑 [weather_bot.py](file:///home/danny/share/weather-bot/weather_bot.py) 文件顶部的配置部分：

```python
# --- 配置部分 ---
# 城市编码 (杭州) - 请替换为你所在城市的 Adcode
CITY_CODE = "330100" 
CITY_NAME = "杭州"
```
*   城市 Adcode 可在 [高德地图行政区划查询](https://lbs.amap.com/api/webservice/guide/api/district) 中查找。

## 📄 License

MIT License