import logging
import asyncio
import random
import requests
import openai
import os
from telegram import Bot
from praw import Reddit
from dotenv import load_dotenv

# 🔹 Загружаем переменные окружения
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

# 🔹 Получение новостей (с разными стилями)
def fetch_latest_news():
    news_list = []
    for source, url in NEWS_SOURCES.items():
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            from xml.etree import ElementTree as ET
            root = ET.fromstring(response.text)
            items = root.findall(".//item")[:3]

            for item in items:
                title = item.find("title").text.strip()
                if len(title) > 100:
                    title = title[:100] + "..."
                news_list.append(title)
        except Exception as e:
            logger.error(f"Ошибка получения новостей с {source}: {e}")

    return news_list

# 🔹 Получение хайповых постов с Reddit (иногда добавляем мемы)
def fetch_reddit_posts():
    subreddits = ["stocks", "technology", "crypto", "finance", "memes", "funny", "programming"]
    posts = []
    try:
        subreddit = random.choice(subreddits)
        logger.info(f"📢 Получаем посты из r/{subreddit}...")
        for submission in reddit.subreddit(subreddit).hot(limit=5):
            if not submission.over_18:
                title = submission.title.strip()
                if len(title) > 100:
                    title = title[:100] + "..."
                posts.append(title)
    except Exception as e:
        logger.error(f"Ошибка получения постов с Reddit: {e}")
    return posts

# 🔹 AI генерация уникального текста (разные стили, инсайды, мемы)
def generate_ai_text(prompt, use_gpt4=False):
    model = "gpt-4-turbo" if use_gpt4 else "gpt-3.5-turbo"
    styles = [
        "Пиши с шутками и мемами",
        "Добавь инсайды и сделай это сенсацией!",
        "Разбери тему аналитически, как эксперт",
        "Напиши так, будто это горячая новость!",
        "Расскажи простыми словами, как для друга",
    ]
    style = random.choice(styles)

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": f"Ты ведешь Telegram-канал. {style}"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=700
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Ошибка генерации текста AI: {e}")
        return "🤖 Ошибка AI. Попробуй позже!"

# 🔹 AI генерация советов по деньгам, крипте и инвестициям
def generate_finance_tips():
    topics = [
        "Какой бизнес запустить в 2025 году?",
        "Стоит ли инвестировать в криптовалюту сейчас?",
        "Как зарабатывать на акциях без риска?",
        "Новые тренды в недвижимости",
        "Какие стартапы сейчас поднимаются?",
        "Как не потерять деньги в инвестициях?",
    ]
    chosen_topic = random.choice(topics)
    return generate_ai_text(f"Дай экспертный совет по теме: {chosen_topic}", use_gpt4=True)

# 🔹 Функция отправки постов в Telegram
async def send_post(bot, text):
    try:
        await bot.send_message(chat_id=CHANNEL_ID, text=text, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка отправки поста в Telegram: {e}")

# 🔹 Генерация контента и постинг
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
                    f"🔥 Разбери эту новость интересно: {selected_news}. Добавь эмоции и инсайды.",
                    use_gpt4=True)
                await send_post(bot, news_text)
            else:
                logger.warning("⚠ Нет свежих новостей")

        elif content_type == "reddit":
            reddit_posts = fetch_reddit_posts()
            if reddit_posts:
                selected_post = random.choice(reddit_posts)
                post_text = generate_ai_text(
                    f"🎭 Дай свой авторский разбор этого поста: {selected_post}. Сделай круто!",
                    use_gpt4=False)
                await send_post(bot, post_text)
            else:
                logger.warning("⚠ Нет актуальных постов на Reddit")

        else:  # Финансовые советы
            tip_text = generate_finance_tips()
            await send_post(bot, tip_text)

        # ⏳ Реалистичный интервал (30 минут - 3 часа)
        delay = random.randint(1800, 10800)
        logger.info(f"⏳ Следующий пост через {delay // 60} минут.")
        await asyncio.sleep(delay)

# 🔹 Запуск бота
async def main():
    bot = Bot(TELEGRAM_TOKEN)
    logger.info("🚀 AI-Бот запущен!")
    await create_and_post_content(bot)

if __name__ == "__main__":
    asyncio.run(main())
