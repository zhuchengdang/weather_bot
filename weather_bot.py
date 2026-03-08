import os
import sys
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# --- 配置部分 ---
# 城市编码 (杭州)
CITY_CODE = "330100"
CITY_NAME = "杭州"

def get_weather_data():
    """获取天气数据"""
    api_key = os.getenv("AMAP_API_KEY")
    if not api_key:
        raise ValueError("未找到 AMAP_API_KEY 环境变量")

    url = "https://restapi.amap.com/v3/weather/weatherInfo"
    params = {
        "city": CITY_CODE,
        "key": api_key,
        "extensions": "base"
    }

    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()

    if data["status"] == "0":
        raise Exception(f"高德API错误: {data.get('info')}")

    return data["lives"][0]

def generate_advice(temp, weather_desc):
    """生成穿衣建议"""
    temp = int(temp)
    advice = ""
    
    if temp < 10:
        advice = "🥶 **寒冷**：厚羽绒服、棉衣、毛衣、围巾。"
    elif 10 <= temp < 15:
        advice = "🧥 **较冷**：风衣、夹克、薄羽绒、长袖衬衫。"
    elif 15 <= temp < 20:
        advice = "👕 **凉爽**：长袖T恤、卫衣、薄外套。"
    elif 20 <= temp < 28:
        advice = "👔 **舒适**：短袖、薄长裙、休闲装。"
    else:
        advice = "🩳 **炎热**：短衣短裤、防晒衣、注意补水。"

    if "雨" in weather_desc:
        advice += "\n☔ **提示**：正在下雨，务必带伞！"
    elif "雪" in weather_desc:
        advice += "\n❄️ **提示**：正在下雪，路滑注意安全！"
    elif "雾" in weather_desc:
        advice += "\n🌫️ **提示**：有雾，能见度低，出行注意交通安全。"
        
    return advice

def send_dingtalk(message_content, markdown_text):
    """发送钉钉通知"""
    webhook = os.getenv("DINGTALK_WEBHOOK")
    secret = os.getenv("DINGTALK_SECRET", "") # 可选：加签密钥
    
    if not webhook:
        print("⚠️ 未配置 DINGTALK_WEBHOOK，跳过钉钉发送。")
        return

    headers = {"Content-Type": "application/json"}
    
    # 构建钉钉 Markdown 消息
    payload = {
        "msgtype": "markdown",
        "markdown": {
            "title": f"{CITY_NAME}天气提醒",
            "text": markdown_text
        },
        "at": {
            "isAtAll": True # @所有人
        }
    }

    # 如果设置了加签密钥，需要计算签名 (简单版暂略，如需安全建议开启加签)
    # 此处仅展示基础发送，若需加签请参考高德/钉钉文档计算 timestamp+sign
    
    try:
        resp = requests.post(webhook, json=payload, headers=headers, timeout=10)
        if resp.json().get("errcode") == 0:
            print("✅ 钉钉消息发送成功")
        else:
            print(f"❌ 钉钉发送失败: {resp.text}")
    except Exception as e:
        print(f"❌ 钉钉请求异常: {e}")

def send_email(subject, html_content):
    """发送邮件通知"""
    smtp_server = os.getenv("EMAIL_SMTP_SERVER")
    smtp_port = int(os.getenv("EMAIL_SMTP_PORT", "465"))
    sender = os.getenv("EMAIL_SENDER")
    password = os.getenv("EMAIL_PASSWORD") # 这里是授权码，不是登录密码
    receiver = os.getenv("EMAIL_RECEIVER") # 接收者邮箱

    if not all([smtp_server, sender, password, receiver]):
        print("⚠️ 邮箱配置不全 (缺少 SMTP_SERVER, SENDER, PASSWORD, RECEIVER)，跳过邮件发送。")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = receiver

    # 纯文本版本
    text_part = MIMEText(html_content.replace("<br>", "\n").replace("**", ""), "plain", "utf-8")
    # HTML 版本
    html_part = MIMEText(html_content, "html", "utf-8")

    msg.attach(text_part)
    msg.attach(html_part)

    try:
        # 尝试 SSL 连接 (端口 465) 或 STARTTLS (端口 587)
        if smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            
        server.login(sender, password)
        server.send_message(msg)
        server.quit()
        print("✅ 邮件发送成功")
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")

def main():
    try:
        print("🌤️  开始获取天气数据...")
        data = get_weather_data()
        
        temp = data["temperature"]
        weather = data["weather"]
        humidity = data["humidity"]
        wind = f"{data['winddirection']}风{data['windpower']}级"
        report_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        advice = generate_advice(temp, weather)

        # 1. 控制台输出 (GitHub Actions 日志)
        print("-" * 30)
        print(f"【{CITY_NAME}天气简报】")
        print(f"时间: {report_time}")
        print(f"温度: {temp}°C | 天气: {weather}")
        print(f"湿度: {humidity}% | 风力: {wind}")
        print(f"建议: {advice}")
        print("-" * 30)

        # 2. 构建钉钉 Markdown 内容
        dingtalk_md = f"""## 🌤️ {CITY_NAME} 天气提醒
> 🕒 时间：{report_time}

| 指标 | 数值 |
| :--- | :--- |
| 🌡️ 温度 | {temp}°C |
| ☁️ 天气 | {weather} |
| 💧 湿度 | {humidity}% |
| 🍃 风力 | {wind} |

### 👗 穿衣建议
{advice}

_数据来源：高德地图_
"""

        # 3. 构建邮件 HTML 内容
        email_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6;">
            <h2 style="color: #2c3e50;">🌤️ {CITY_NAME} 天气提醒</h2>
            <p><strong>🕒 更新时间:</strong> {report_time}</p>
            <div style="background-color: #f9f9f9; padding: 15px; border-radius: 8px; border-left: 5px solid #3498db;">
                <p><strong>🌡️ 当前温度:</strong> {temp}°C</p>
                <p><strong>☁️ 天气状况:</strong> {weather}</p>
                <p><strong>💧 相对湿度:</strong> {humidity}%</p>
                <p><strong>🍃 风向风力:</strong> {wind}</p>
            </div>
            <h3 style="color: #e67e22;">👗 穿衣建议</h3>
            <p style="font-size: 16px; color: #333;">{advice.replace(chr(10), "<br>")}</p>
            <hr>
            <p style="font-size: 12px; color: #999;">自动发送 by GitHub Actions</p>
        </body>
        </html>
        """

        # 4. 发送通知
        print("📤 正在发送通知...")
        send_dingtalk(advice, dingtalk_md)
        send_email(f"【{CITY_NAME}天气】{weather} {temp}°C - {report_time}", email_html)
        
        print("🎉 任务完成")

    except Exception as e:
        print(f"❌ 程序运行出错: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()