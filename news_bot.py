import feedparser
import requests
from datetime import datetime
import pytz
import os

KST = pytz.timezone('Asia/Seoul')
today = datetime.now(KST).strftime('%Y-%m-%d')

WEBHOOK_URL = os.environ['TEAMS_WEBHOOK_URL']

FEEDS = [
    {
        "label": "🇰🇷 국내 VC 뉴스",
        "url": "https://news.google.com/rss/search?q=벤처캐피탈+스타트업+투자&hl=ko&gl=KR&ceid=KR:ko",
        "max_items": 7
    },
    {
        "label": "🎬 영화 업계 뉴스",
        "url": "https://news.google.com/rss/search?q=영화+OR+OTT+OR+넷플릭스+OR+드라마+OR+콘텐츠+OR+박스오피스&hl=ko&gl=KR&ceid=KR:ko",
        "max_items": 5
    },
    {
        "label": "📈 경제/금융 뉴스",
        "url": "https://news.google.com/rss/search?q=경제+금융+증시&hl=ko&gl=KR&ceid=KR:ko",
        "max_items": 5
    },
    {
        "label": "🌐 글로벌 VC 뉴스",
        "url": "https://news.google.com/rss/search?q=venture+capital+startup+funding&hl=en&gl=US&ceid=US:en",
        "max_items": 4
    }
]

BLOCKED = ['instagram.com', 'twitter.com', 'facebook.com']

def get_news(feed_url, max_items=5):
    feed = feedparser.parse(feed_url)
    results = []
    for entry in feed.entries:
        pub = entry.get('published', '')
        if today not in pub and datetime.now(KST).strftime('%d %b %Y') not in pub:
            continue
        if any(b in entry.get('link', '') + entry.get('title', '') for b in BLOCKED):
            continue
        results.append((entry.title, entry.get('link', '')))
        if len(results) >= max_items:
            break
    return results

message = f"📊 오늘의 뉴스 ({today})\n\n"

for feed in FEEDS:
    news = get_news(feed['url'], feed['max_items'])
    message += f"{feed['label']}\n"
    if news:
        for i, (title, link) in enumerate(news, 1):
            message += f"{i}. [{title}]({link})\n"
    else:
        message += "오늘 뉴스가 없습니다.\n"
    message += "\n"

payload = {
    "type": "message",
    "attachments": [
        {
            "contentType": "application/vnd.microsoft.card.adaptive",
            "content": {
                "type": "AdaptiveCard",
                "version": "1.2",
                "body": [
                    {
                        "type": "TextBlock",
                        "text": message,
                        "wrap": True
                    }
                ]
            }
        }
    ]
}

requests.post(WEBHOOK_URL, json=payload)
print("전송 완료!")
