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

# 🔹 Источники новостей
NEWS_SOURCES = {
    "Yahoo Finance": "https://finance.yahoo.com/rss/topstories",
    "BBC News": "http://feeds.bbci.co.uk/news/rss.xml",
    "TechCrunch": "https://techcrunch.com/feed/",
    "Crypto News": "https://cryptonews.com/news/feed/",
}

# 🔹 Получение новостей (с ограничением длины)
def fetch_latest_news():
    news_list = []
    for source, url in NEWS_SOURCES.items():
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            from xml.etree import ElementTree as ET
            root = ET.fromstring(response.text)
            items = root.findall(".//item")[:3]  # Берем 3 самые свежие новости

            for item in items:
                title = item.find("title").text.strip()
                if len(title) > 100:  # Ограничиваем длину заголовка
                    title = title[:100] + "..."
                news_list.append(title)
        except Exception as e:
            logger.error(f"Ошибка получения новостей с {source}: {e}")

    return news_list

# 🔹 Получение хайповых постов с Reddit
def fetch_reddit_posts(subreddits, limit=3):
    posts = []
    try:
        for subreddit in subreddits:
            logger.info(f"📢 Получаем посты из r/{subreddit}...")
            for submission in reddit.subreddit(subreddit).hot(limit=limit):
                if not submission.over_18:
                    title = submission.title.strip()
                    if len(title) > 100:  # Ограничиваем длину заголовка
                        title = title[:100] + "..."
                    posts.append(title)
    except Exception as e:
        logger.error(f"Ошибка получения постов с Reddit: {e}")
    return posts

# 🔹 AI генерация текста (GPT-4 для аналитики, GPT-3.5 для мемов)
def generate_ai_text(prompt, use_gpt4=False):
    model = "gpt-4-turbo" if use_gpt4 else "gpt-3.5-turbo"

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Ты ведешь Telegram-канал. Пиши интересно, добавляй эмоции и инсайды."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Ошибка генерации текста AI: {e}")
        return "🤖 Ошибка AI. Обсудим в комментариях!"

# 🔹 AI генерация советов по деньгам и инвестициям
def generate_finance_tips():
    topics = [
        "Лучшие способы пассивного дохода в 2025 году",
        "Почему важно инвестировать в себя?",
        "Какие активы защищают деньги от инфляции?",
        "Как минимизировать риски при инвестициях?",
        "Ошибки начинающих инвесторов и как их избежать"
    ]
    chosen_topic = random.choice(topics)
    return generate_ai_text(f"Дай экспертный совет на тему: {chosen_topic}", use_gpt4=True)

# 🔹 Функция отправки постов
async def send_post(bot, text):
    try:
        await bot.send_message(chat_id=CHANNEL_ID, text=text, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка отправки поста в Telegram: {e}")

# 🔹 Главная функция генерации контента и постинга
async def create_and_post_content(bot):
    while True:
        logger.info("📢 Генерация нового AI-контента...")

        content_choices = ["news", "reddit", "finance_tips"]
        content_type = random.choice(content_choices)

        if content_type == "news":
            latest_news = fetch_latest_news()
            if latest_news:
                selected_news = random.choice(latest_news)
                news_text = generate_ai_text(
                    f"Разбери эту новость кратко: {selected_news}. Добавь мнение и инсайды.",
                    use_gpt4=True)
                await send_post(bot, news_text)
            else:
                logger.warning("⚠ Нет свежих новостей")

        elif content_type == "reddit":
            reddit_posts = fetch_reddit_posts(["stocks", "technology", "crypto", "finance"], limit=3)
            if reddit_posts:
                selected_post = random.choice(reddit_posts)
                post_text = generate_ai_text(
                    f"Дай свой краткий разбор поста: {selected_post}. Пиши живо и интересно.",
                    use_gpt4=False)
                await send_post(bot, post_text)
            else:
                logger.warning("⚠ Нет актуальных постов на Reddit")

        else:  # Финансовые советы
            tip_text = generate_finance_tips()
            await send_post(bot, tip_text)

        # ⏳ Реалистичный интервал (от 30 минут до 5 часов)
        delay = random.randint(1800, 10800)  # Уменьшил макс. интервал до 3 часов
        logger.info(f"⏳ Следующий пост через {delay // 60} минут.")
        await asyncio.sleep(delay)

# 🔹 Запуск бота
async def main():
    bot = Bot(TELEGRAM_TOKEN)
    logger.info("🚀 AI-Бот запущен!")
    await create_and_post_content(bot)

if __name__ == "__main__":
    asyncio.run(main())
