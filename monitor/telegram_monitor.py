import asyncio
import logging
import os
from datetime import datetime, timedelta

import requests
from dotenv import load_dotenv
from pymongo import MongoClient
from telethon import TelegramClient, events
from telethon.tl.types import Channel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
PHONE = os.getenv('PHONE')
BOT_TOKEN = os.getenv('BOT_TOKEN')
NOTIFICATION_CHAT_ID = os.getenv('NOTIFICATION_CHAT_ID')
MONGODB_URI = os.getenv('MONGODB_URI')
MONGODB_DB = os.getenv('MONGODB_DB')

mongo_client = MongoClient(MONGODB_URI)
db = mongo_client[MONGODB_DB]
channels_collection = db.channels
notifications_collection = db.notifications
processed_messages_collection = db.processed_messages

event_handlers = []


async def send_bot_notification(message):
    try:
        logger.info(f"Отправка уведомления: {message}")
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {"chat_id": NOTIFICATION_CHAT_ID, "text": message, "parse_mode": "HTML"}
        response = requests.post(url, json=data)
        if response.status_code != 200:
            logger.error(f"Ошибка отправки уведомления: {response.text}")
    except Exception as e:
        logger.error(f"Ошибка при отправке уведомления: {str(e)}")


async def check_keywords(text, keywords):
    if not text or not keywords:
        return False
    text = text.lower()
    return any(keyword.lower() in text for keyword in keywords)


async def message_handler(event):
    try:
        message_id = f"{event.chat_id}_{event.message.id}"
        if processed_messages_collection.find_one({'message_id': message_id}):
            return

        processed_messages_collection.insert_one(
            {'message_id': message_id, 'chat_id': event.chat_id, 'message_id_original': event.message.id,
                'processed_at': datetime.now(), 'text': event.message.text})

        chat = await event.get_chat()
        chat_name = chat.title if hasattr(chat, 'title') else chat.first_name
        chat_id = chat.id

        if isinstance(chat, Channel) and chat_id > 0:
            chat_id = -1000000000000 - chat_id

        chat_data = channels_collection.find_one({'chat_id': chat_id})
        if not chat_data or not chat_data.get('keywords'):
            return

        message_text = event.message.text or ""
        if await check_keywords(message_text, chat_data['keywords']):
            notification = f"🔔 <b>Новое сообщение в {chat_data['type']} {chat_name}</b>\n\n"
            notification += f"<b>Текст:</b> {message_text}\n"
            if event.message.media:
                notification += "📎 <b>Сообщение содержит медиафайл</b>\n"

            await send_bot_notification(notification)
            notifications_collection.insert_one(
                {'chat_id': chat_id, 'message_id': event.message.id, 'text': message_text,
                    'keywords': chat_data['keywords'], 'notification_text': notification, 'created_at': datetime.now()})
    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения: {str(e)}")
        await send_bot_notification(f"❌ Ошибка при обработке сообщения: {str(e)}")


async def update_chat_ids(client):
    while True:
        try:
            chats = channels_collection.find()
            current_chat_ids = [chat['chat_id'] for chat in chats]

            for handler in event_handlers:
                client.remove_event_handler(handler)
            event_handlers.clear()

            if current_chat_ids:
                for chat_id in current_chat_ids:
                    try:
                        chat = await client.get_entity(chat_id)
                        logger.info(
                            f"Доступ к чату {chat.title if hasattr(chat, 'title') else chat.first_name} (ID: {chat_id})")
                    except Exception as e:
                        logger.error(f"Ошибка доступа к чату {chat_id}: {str(e)}")

                handler = client.add_event_handler(message_handler, events.NewMessage(chats=current_chat_ids))
                event_handlers.append(handler)

                handler = client.add_event_handler(message_handler,
                    events.NewMessage(chats=current_chat_ids, pattern=None))
                event_handlers.append(handler)
        except Exception as e:
            logger.error(f"Ошибка при обновлении списка чатов: {str(e)}")
        await asyncio.sleep(60)


async def cleanup_old_records():
    while True:
        try:
            week_ago = datetime.now() - timedelta(days=7)
            processed_messages_collection.delete_many({'processed_at': {'$lt': week_ago}})
            notifications_collection.delete_many({'created_at': {'$lt': week_ago}})
        except Exception as e:
            logger.error(f"Ошибка при очистке старых записей: {str(e)}")
        await asyncio.sleep(3600)


async def main():
    try:
        client = TelegramClient('session', API_ID, API_HASH)
        await client.start(phone=PHONE)
        logger.info("Монитор запущен")
        await send_bot_notification("🟢 Монитор запущен")

        asyncio.create_task(cleanup_old_records())
        asyncio.create_task(update_chat_ids(client))

        await client.run_until_disconnected()
    except Exception as e:
        logger.error(f"Критическая ошибка: {str(e)}")
        await send_bot_notification(f"❌ Критическая ошибка: {str(e)}")


if __name__ == '__main__':
    asyncio.run(main())
