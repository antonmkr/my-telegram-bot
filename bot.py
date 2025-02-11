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

# 🔹 Источники новостей (убрали BBC)
NEWS_SOURCES = {
    "Yahoo Finance": "https://finance.yahoo.com/rss/topstories",
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
                news_list.append(title)
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
                    posts.append(title)
    except Exception as e:
        logger.error(f"Ошибка получения постов с Reddit: {e}")
    return posts

# 🔹 Генерация AI-текста без ограничений, которые портят форматирование
def generate_ai_text(prompt, use_gpt4=False):
    model = "gpt-4-turbo" if use_gpt4 else "gpt-3.5-turbo"
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Ты ведешь Telegram-канал. Пиши живым языком, добавляй инсайды, юмор и эмоции."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Ошибка AI: {e}")
        return "Что-то пошло не так. Пишите в комменты!"

# 🔹 Список тем для AI-аналитики
finance_topics = [
    "Как создать пассивный доход в 2025?",
    "Какие активы лучше всего защитят от инфляции?",
    "Куда вложить деньги, если у тебя всего 1000$?",
    "Какие акции сейчас недооценены?",
    "5 главных ошибок начинающих инвесторов",
    "Как крупные фонды управляют миллиардами?",
    "Будущее крипты: какие монеты перспективны?",
    "Лучшие стратегии для торговли на рынке"
]

def generate_finance_tips():
    return generate_ai_text(f"Расскажи просто и понятно: {random.choice(finance_topics)}", use_gpt4=True)

# 🔹 Дополнительные AI-функции
def generate_market_analysis():
    return generate_ai_text("Дай простой обзор рынка на сегодня: главные события и тренды.", use_gpt4=True)

def generate_crypto_trends():
    return generate_ai_text("Свежие тренды в криптовалюте: какие монеты сейчас на хайпе?", use_gpt4=True)

def generate_investment_hacks():
    return generate_ai_text("Расскажи инвестиционные лайфхаки, которые помогут заработать.", use_gpt4=True)

def generate_real_estate_tips():
    return generate_ai_text("Как выгодно вложиться в недвижимость в 2025 году?", use_gpt4=True)

# 🔹 Контентные категории
content_choices = [
    "news", "reddit", "finance_tips", "crypto_insights", "market_analysis",
    "crypto_trends", "investment_hacks", "real_estate_tips"
]

# 🔹 Форматирование текста перед отправкой (без Telegram-разметки)
def clean_and_format_text(text):
    text = text.replace("🤖", "📊")  # Заменяем нейтральным эмодзи
    text = "\n".join([line.strip() for line in text.split("\n") if line.strip()])  # Убираем лишние переносы строк
    return text

# 🔹 Функция отправки сообщений
async def send_post(bot, text):
    try:
        formatted_text = clean_and_format_text(text)
        await bot.send_message(chat_id=CHANNEL_ID, text=formatted_text, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка отправки поста: {e}")

# 🔹 Алгоритм выбора контента
async def create_and_post_content(bot):
    while True:
        logger.info("📢 Генерация контента...")
        content_type = random.choice(content_choices)

        if content_type == "news":
            latest_news = fetch_latest_news()
            if latest_news:
                selected_news = random.choice(latest_news)
                news_text = generate_ai_text(f"Что думаешь про эту новость? {selected_news}", use_gpt4=True)
                await send_post(bot, news_text)

        elif content_type == "reddit":
            reddit_posts = fetch_reddit_posts(["stocks", "technology", "crypto", "finance", "economy", "wallstreetbets"], limit=5)
            if reddit_posts:
                selected_post = random.choice(reddit_posts)
                post_text = generate_ai_text(f"Что думаешь об этом посте? {selected_post}", use_gpt4=False)
                await send_post(bot, post_text)

        elif content_type == "finance_tips":
            await send_post(bot, generate_finance_tips())

        elif content_type == "crypto_insights":
            await send_post(bot, generate_crypto_trends())

        elif content_type == "market_analysis":
            await send_post(bot, generate_market_analysis())

        delay = random.randint(1800, 7200)  # От 30 минут до 2 часов
        logger.info(f"⏳ Следующий пост через {delay // 60} минут.")
        await asyncio.sleep(delay)

# 🔹 Запуск бота
async def main():
    bot = Bot(TELEGRAM_TOKEN)
    logger.info("🚀 Бот запущен!")
    await create_and_post_content(bot)

if __name__ == "__main__":
    asyncio.run(main())
