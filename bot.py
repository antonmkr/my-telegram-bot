import logging
import asyncio
import random
import requests
import openai
from telegram import Bot
from praw import Reddit

import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()
client = openai.Client()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")

CHANNEL_ID = "@gachistocks"

# 🔹 Reddit API Credentials
REDDIT_USER_AGENT = "MyTelegramBot/0.1 by defiler16"

openai.api_key = OPENAI_API_KEY

# 🔹 Настройка логов
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# 🔹 Настройка API Reddit
reddit = Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent=REDDIT_USER_AGENT,
)

# 🔹 Источники новостей (новые добавлены)
NEWS_SOURCES = {
    "Yahoo Finance": "https://finance.yahoo.com/rss/topstories",
    "BBC News": "http://feeds.bbci.co.uk/news/rss.xml",
    "TechCrunch": "https://techcrunch.com/feed/",
    "Crypto News": "https://cryptonews.com/news/feed/",
    "CNBC": "https://www.cnbc.com/id/100003114/device/rss/rss.html",
    "Bloomberg": "https://www.bloomberg.com/feeds/podcast.xml",
    "Wall Street Journal": "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
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
            items = root.findall(".//item")[:5]  # Увеличено до 5 новостей

            for item in items:
                title = item.find("title").text.strip()
                if len(title) > 120:
                    title = title[:120] + "..."
                news_list.append(title)
        except Exception as e:
            logger.error(f"Ошибка получения новостей с {source}: {e}")

    return news_list

# 🔹 Получение топовых постов с Reddit (добавлено больше сабреддитов)
def fetch_reddit_posts(subreddits, limit=5):
    posts = []
    try:
        for subreddit in subreddits:
            logger.info(f"📢 Получаем посты из r/{subreddit}...")
            for submission in reddit.subreddit(subreddit).hot(limit=limit):
                if not submission.over_18:
                    title = submission.title.strip()
                    if len(title) > 120:
                        title = title[:120] + "..."
                    posts.append(title)
    except Exception as e:
        logger.error(f"Ошибка получения постов с Reddit: {e}")
    return posts

# 🔹 AI генерация текста
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

# 🔹 Темы для финансовых советов (расширенный список)
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

# 🔹 Выбор случайного совета
def generate_finance_tips():
    chosen_topic = random.choice(finance_topics)
    return generate_ai_text(f"Дай экспертный совет по теме: {chosen_topic}", use_gpt4=True)

# 🔹 Опции контента
content_choices = ["news", "reddit", "finance_tips", "crypto_insights", "business_strategies"]

# 🔹 Функция отправки постов
async def send_post(bot, text):
    try:
        await bot.send_message(chat_id=CHANNEL_ID, text=text, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка отправки поста: {e}")

# 🔹 Генерация и постинг контента
async def create_and_post_content(bot):
    while True:
        logger.info("📢 Генерация AI-контента...")

        content_type = random.choice(content_choices)

        if content_type == "news":
            latest_news = fetch_latest_news()
            if latest_news:
                selected_news = random.choice(latest_news)
                news_text = generate_ai_text(
                    f"Разбери новость кратко: {selected_news}. Добавь мнение и инсайды.",
                    use_gpt4=True)
                await send_post(bot, news_text)

        elif content_type == "reddit":
            reddit_posts = fetch_reddit_posts(["stocks", "technology", "crypto", "finance", "economy", "wallstreetbets"], limit=5)
            if reddit_posts:
                selected_post = random.choice(reddit_posts)
                post_text = generate_ai_text(
                    f"Разбери Reddit-пост: {selected_post}. Пиши интересно и с анализом.",
                    use_gpt4=False)
                await send_post(bot, post_text)

        elif content_type == "finance_tips":
            tip_text = generate_finance_tips()
            await send_post(bot, tip_text)

        elif content_type == "crypto_insights":
            insight_text = generate_ai_text(
                "Дай свежий инсайд о криптовалютах, трендах и прогнозах.",
                use_gpt4=True)
            await send_post(bot, insight_text)

        elif content_type == "business_strategies":
            strategy_text = generate_ai_text(
                "Поделись бизнес-стратегией, которая поможет заработать в 2025 году.",
                use_gpt4=True)
            await send_post(bot, strategy_text)

        delay = random.randint(1800, 7200)  # Интервал от 30 минут до 2 часов
        logger.info(f"⏳ Следующий пост через {delay // 60} минут.")
        await asyncio.sleep(delay)

# 🔹 Запуск бота
async def main():
    bot = Bot(TELEGRAM_TOKEN)
    logger.info("🚀 AI-Бот запущен!")
    await create_and_post_content(bot)

if __name__ == "__main__":
    asyncio.run(main())
