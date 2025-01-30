import logging
import asyncio
import random
import requests
import openai
from telegram import Bot
from praw import Reddit
import os
from dotenv import load_dotenv

# 🔹 Загружаем переменные окружения
load_dotenv()
client = openai.Client()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")

CHANNEL_ID = "@gachistocks"
openai.api_key = OPENAI_API_KEY

# 🔹 Настройка логов
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# 🔹 Настройка API Reddit
reddit = Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent="MyTelegramBot/0.1 by defiler16",
)

# 🔹 Источники новостей
NEWS_SOURCES = {
    "Yahoo Finance": "https://finance.yahoo.com/rss/topstories",
    "BBC News": "http://feeds.bbci.co.uk/news/rss.xml",
    "TechCrunch": "https://techcrunch.com/feed/",
    "Crypto News": "https://cryptonews.com/news/feed/",
    "CNBC": "https://www.cnbc.com/id/100003114/device/rss/rss.html",
    "Bloomberg": "https://www.bloomberg.com/feeds/podcast.xml",
    "Wall Street Journal": "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
    "Investing.com": "https://www.investing.com/rss/news.rss",
    "Forbes": "https://www.forbes.com/investing/feed/",
    "Financial Times": "https://www.ft.com/rss/home",
    "MarketWatch": "https://www.marketwatch.com/rss/topstories",
    "The Economist": "https://www.economist.com/latest/rss.xml"
}

# 🔹 Получение новостей
def fetch_latest_news():
    news_list = []
    for source, url in NEWS_SOURCES.items():
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            from xml.etree import ElementTree as ET
            root = ET.fromstring(response.text)
            items = root.findall(".//item")[:5]

            for item in items:
                title = item.find("title").text.strip()
                news_list.append(title[:120] + "..." if len(title) > 120 else title)
        except Exception as e:
            logger.error(f"Ошибка получения новостей с {source}: {e}")
    return news_list

# 🔹 Получение постов с Reddit
def fetch_reddit_posts(subreddits, limit=5):
    posts = []
    try:
        for subreddit in subreddits:
            for submission in reddit.subreddit(subreddit).hot(limit=limit):
                if not submission.over_18:
                    title = submission.title.strip()
                    posts.append(title[:120] + "..." if len(title) > 120 else title)
    except Exception as e:
        logger.error(f"Ошибка получения постов с Reddit: {e}")
    return posts

# 🔹 Генерация AI-текста
def generate_ai_text(prompt, use_gpt4=False):
    model = "gpt-4-turbo" if use_gpt4 else "gpt-3.5-turbo"
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Ты ведешь Telegram-канал. Пиши живо, добавляй инсайды, делай посты вовлекающими."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1200
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Ошибка AI: {e}")
        return "🤖 Ошибка AI. Обсудим в комментариях!"

# 🔹 Расширенный список тем для AI-аналитики
finance_topics = [
    "Лучшие способы пассивного дохода в 2025 году",
    "Почему важно инвестировать в себя?",
    "Какие активы защищают деньги от инфляции?",
    "Как минимизировать риски при инвестициях?",
    "Ошибки начинающих инвесторов и как их избежать",
    "Будущее фондового рынка: какие тренды учитывать?",
    "Как правильно диверсифицировать портфель?",
    "Стоит ли инвестировать в криптовалюту?",
    "Психология инвестирования: как не поддаваться панике?",
    "Лучшие инвестиционные стратегии 2025 года"
]

def generate_finance_tips():
    return generate_ai_text(f"Дай экспертный совет по теме: {random.choice(finance_topics)}", use_gpt4=True)

# 🔹 Дополнительные AI-функции
def generate_market_analysis():
    return generate_ai_text("Дай краткий обзор фондового рынка на сегодня: индексы, тренды, перспективы.", use_gpt4=True)

def generate_crypto_trends():
    return generate_ai_text("Обзор свежих трендов в криптовалюте: топовые токены, прогнозы, инсайды.", use_gpt4=True)

def generate_investment_hacks():
    return generate_ai_text("Поделись топовыми лайфхаками для инвесторов, которые мало кто знает.", use_gpt4=True)

def generate_real_estate_tips():
    return generate_ai_text("Какие инвестиционные стратегии в недвижимости будут актуальны в 2025 году?", use_gpt4=True)

# 🔹 Расширенный список контентных категорий
content_choices = [
    "news", "reddit", "finance_tips", "crypto_insights", "business_strategies",
    "market_analysis", "crypto_trends", "investment_hacks", "real_estate_tips"
]

# 🔹 Форматирование текста перед отправкой
def clean_and_format_text(text):
    text = text.replace("\n\n", "\n")
    text = text.replace("🤖", "📊")
    return text[:990] + "..." if len(text) > 1000 else text

async def send_post(bot, text):
    try:
        formatted_text = clean_and_format_text(text)
        await bot.send_message(chat_id=CHANNEL_ID, text=formatted_text, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка отправки поста: {e}")

# 🔹 Алгоритм выбора контента
async def create_and_post_content(bot):
    while True:
        logger.info("📢 Генерация AI-контента...")
        content_type = random.choices(content_choices, weights=[3, 3, 3, 2, 2, 2, 2, 2, 1], k=1)[0]

        if content_type == "news":
            latest_news = fetch_latest_news()
            if latest_news:
                await send_post(bot, generate_ai_text(f"Разбери новость кратко: {random.choice(latest_news)}", use_gpt4=True))

        elif content_type == "reddit":
            reddit_posts = fetch_reddit_posts(["stocks", "technology", "crypto", "finance", "economy", "wallstreetbets"], limit=5)
            if reddit_posts:
                await send_post(bot, generate_ai_text(f"Разбери Reddit-пост: {random.choice(reddit_posts)}", use_gpt4=False))

        elif content_type == "finance_tips":
            await send_post(bot, generate_finance_tips())

        elif content_type == "crypto_insights":
            await send_post(bot, generate_crypto_trends())

        elif content_type == "market_analysis":
            await send_post(bot, generate_market_analysis())

        delay = random.randint(1800, 7200)
        logger.info(f"⏳ Следующий пост через {delay // 60} минут.")
        await asyncio.sleep(delay)

# 🔹 Запуск бота
async def main():
    bot = Bot(TELEGRAM_TOKEN)
    logger.info("🚀 AI-Бот запущен!")
    await create_and_post_content(bot)

if __name__ == "__main__":
    asyncio.run(main())
