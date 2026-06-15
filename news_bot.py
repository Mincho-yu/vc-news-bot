import feedparser
import requests
from datetime import datetime
import pytz
import os
import re
import random

KST = pytz.timezone('Asia/Seoul')
today = datetime.now(KST).strftime('%Y-%m-%d')

WEBHOOK_URL = os.environ['TEAMS_WEBHOOK_URL']

FEEDS = [
    {
        "label": "🇰🇷 국내 VC 뉴스",
        "urls": [
            "https://news.google.com/rss/search?q=벤처캐피탈&hl=ko&gl=KR&ceid=KR:ko",
            "https://news.google.com/rss/search?q=스타트업+투자유치&hl=ko&gl=KR&ceid=KR:ko",
            "https://news.google.com/rss/search?q=시리즈A+OR+시리즈B&hl=ko&gl=KR&ceid=KR:ko",
            "https://news.google.com/rss/search?q=벤처투자+OR+엑셀러레이터&hl=ko&gl=KR&ceid=KR:ko"
        ],
        "max_items": 7
    },
    {
        "label": "🎬 영화 업계 뉴스",
        "urls": [
            "https://news.google.com/rss/search?q=영화+박스오피스&hl=ko&gl=KR&ceid=KR:ko",
            "https://news.google.com/rss/search?q=OTT+넷플릭스&hl=ko&gl=KR&ceid=KR:ko",
            "https://news.google.com/rss/search?q=드라마+제작&hl=ko&gl=KR&ceid=KR:ko",
            "https://news.google.com/rss/search?q=K콘텐츠+OR+한류&hl=ko&gl=KR&ceid=KR:ko"
        ],
        "max_items": 5
    },
    {
        "label": "📈 경제/금융 뉴스",
        "urls": [
            "https://news.google.com/rss/search?q=코스피+OR+증시&hl=ko&gl=KR&ceid=KR:ko",
            "https://news.google.com/rss/search?q=부동산+OR+아파트&hl=ko&gl=KR&ceid=KR:ko",
            "https://news.google.com/rss/search?q=금리+OR+환율&hl=ko&gl=KR&ceid=KR:ko",
            "https://news.google.com/rss/search?q=기업실적+OR+자산운용&hl=ko&gl=KR&ceid=KR:ko"
        ],
        "max_items": 5
    },
    {
        "label": "🌐 글로벌 VC 뉴스",
        "urls": [
            "https://news.google.com/rss/search?q=venture+capital+funding&hl=en&gl=US&ceid=US:en",
            "https://news.google.com/rss/search?q=startup+series+round&hl=en&gl=US&ceid=US:en",
            "https://news.google.com/rss/search?q=unicorn+startup&hl=en&gl=US&ceid=US:en"
        ],
        "max_items": 4
    }
]

BLOCKED = ['instagram.com', 'twitter.com', 'facebook.com']

SPAM_KEYWORDS = [
    '모집', '참가기업', '참가자', '신청', '접수', '공지', '안내',
    '세미나', '컨퍼런스', '포럼', '웨비나', '간담회', '워크숍', '워크샵',
    '개최', '주최', '주관', '후원', '특강', '강연',
    '이벤트', '프로모션', '할인', '광고', '협찬',
    '플랫 레터', '뉴스레터',
    '공모', '시상', '시상식', '시상자', '수상',
    '채용', '구인', '모집공고'
]

def is_spam(title):
    title_lower = title.lower()
    return any(kw.lower() in title_lower for kw in SPAM_KEYWORDS)

def get_keywords(title):
    clean = title.split(' - ')[0]
    clean = re.sub(r'[^\w\s가-힣a-zA-Z]', ' ', clean)
    words = [w.lower() for w in clean.split() if len(w) >= 2]
    return set(words)

def is_duplicate(new_title, existing_titles, threshold=0.5):
    new_kw = get_keywords(new_title)
    if not new_kw:
        return False
    for existing in existing_titles:
        existing_kw = get_keywords(existing)
        if not existing_kw:
            continue
        overlap = len(new_kw & existing_kw)
        smaller = min(len(new_kw), len(existing_kw))
        if smaller > 0 and overlap / smaller >= threshold:
            return True
    return False

def get_news_from_multiple(urls, max_items=5):
    """여러 URL에서 뉴스를 수집해 섞어서 다양하게"""
    all_entries = []
    now_kst = datetime.now(KST)
    today_formats = [
        now_kst.strftime('%Y-%m-%d'),
        now_kst.strftime('%d %b %Y'),
        now_kst.strftime('%a, %d %b %Y'),
    ]
    yesterday_utc = datetime.now(pytz.UTC).strftime('%d %b %Y')
    
    for url in urls:
        feed = feedparser.parse(url)
        for entry in feed.entries[:10]:  # URL당 상위 10개만
            pub = entry.get('published', '')
            if not any(t in pub for t in today_formats) and yesterday_utc not in pub:
                continue
            if any(b in entry.get('link', '') + entry.get('title', '') for b in BLOCKED):
                continue
            if is_spam(entry.title):
                continue
            all_entries.append((entry.title, entry.get('link', '')))
    
    # 섞기 (다양성 확보)
    random.shuffle(all_entries)
    
    # 중복 제거하면서 max_items까지 추리기
    results = []
    for title, link in all_entries:
        if is_duplicate(title, [t for t, _ in results]):
            continue
        results.append((title, link))
        if len(results) >= max_items:
            break
    return results

message = f"📊 오늘의 뉴스 ({today})\n\n"

for feed in FEEDS:
    news = get_news_from_multiple(feed['urls'], feed['max_items'])
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
