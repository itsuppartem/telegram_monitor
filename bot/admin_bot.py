import asyncio
import logging
import os
from datetime import datetime
from typing import List, Dict

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv
from pymongo import MongoClient
from telethon import TelegramClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
MONGODB_URI = os.getenv('MONGODB_URI')
MONGODB_DB = os.getenv('MONGODB_DB')
API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')

mongo_client = MongoClient(MONGODB_URI)
db = mongo_client[MONGODB_DB]
channels_collection = db.channels
keywords_collection = db.keywords
notifications_collection = db.notifications
messages_collection = db.messages

telethon_client = TelegramClient('session', API_ID, API_HASH)

ITEMS_PER_PAGE = 5


class BotStates(StatesGroup):
    waiting_for_forward = State()
    waiting_keywords = State()


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


async def delete_previous_messages(user_id: int):
    """Удаляет предыдущие сообщения бота"""
    try:
        user_messages = messages_collection.find({'user_id': user_id})
        message_ids = [msg['message_id'] for msg in user_messages]

        if message_ids:
            for message_id in message_ids:
                try:
                    await bot.delete_message(chat_id=user_id, message_id=message_id)
                except Exception as e:
                    logger.error(f"Error deleting message {message_id}: {str(e)}")

            messages_collection.delete_many({'user_id': user_id})
    except Exception as e:
        logger.error(f"Error deleting messages: {str(e)}")


async def save_message_id(user_id: int, message_id: int):
    """Сохраняет ID сообщения в MongoDB"""
    try:
        messages_collection.insert_one({'user_id': user_id, 'message_id': message_id, 'timestamp': datetime.now()})
    except Exception as e:
        logger.error(f"Error saving message ID: {str(e)}")


async def send_message(chat_id: int, text: str, reply_markup=None):
    """Отправляет новое сообщение, предварительно удалив старые"""
    await delete_previous_messages(chat_id)
    message = await bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)
    await save_message_id(chat_id, message.message_id)
    return message


def get_channels_page(page: int = 0) -> tuple[List[Dict], int]:
    """Получает страницу чатов и общее количество страниц"""
    channels = list(channels_collection.find())
    total_pages = (len(channels) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    start_idx = page * ITEMS_PER_PAGE
    end_idx = start_idx + ITEMS_PER_PAGE
    return channels[start_idx:end_idx], total_pages


def get_main_menu_keyboard(page: int = 0) -> InlineKeyboardMarkup:
    """Создает клавиатуру главного меню с пагинацией"""
    channels, total_pages = get_channels_page(page)

    keyboard = []
    for channel in channels:
        keyboard.append([InlineKeyboardButton(text=f"{'👤' if channel['type'] == 'user' else '💬'} {channel['title']}",
            callback_data=f"channel_info_{channel['chat_id']}")])

    pagination_buttons = []
    if page > 0:
        pagination_buttons.append(InlineKeyboardButton(text="⬅️", callback_data=f"page_{page - 1}"))
    if page < total_pages - 1:
        pagination_buttons.append(InlineKeyboardButton(text="➡️", callback_data=f"page_{page + 1}"))

    if pagination_buttons:
        keyboard.append(pagination_buttons)

    keyboard.append([InlineKeyboardButton(text="➕ Добавить чат", callback_data="add")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_channel_info_keyboard(chat_id: int) -> InlineKeyboardMarkup:
    """Создает клавиатуру с действиями для чата"""
    keyboard = [[InlineKeyboardButton(text="📝 Изменить ключевые слова", callback_data=f"set_keywords_{chat_id}")],
        [InlineKeyboardButton(text="❌ Удалить чат", callback_data=f"confirm_delete_{chat_id}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back")]]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    allowed_ids = [int(id) for id in os.getenv('ALLOWED_IDS', '').split(',') if id]
    if message.from_user.id not in allowed_ids:
        await message.answer("⛔️ У вас нет доступа к этому боту.")
        return

    await send_message(message.chat.id, "Выберите чат для управления:", reply_markup=get_main_menu_keyboard())


@dp.callback_query(F.data.startswith("page_"))
async def handle_pagination(callback: types.CallbackQuery):
    page = int(callback.data.split('_')[1])
    await send_message(callback.message.chat.id, "Выберите чат для управления:",
        reply_markup=get_main_menu_keyboard(page))


@dp.callback_query(F.data.startswith("channel_info_"))
async def show_channel_info(callback: types.CallbackQuery):
    chat_id = int(callback.data.split('_')[2])
    channel = channels_collection.find_one({'chat_id': chat_id})
    if channel:
        message_text = (f"📋 Информация о чате:\n\n"
                        f"Название: {channel['title']}\n"
                        f"ID: {channel['chat_id']}\n"
                        f"Тип: {channel['type']}\n")
        if channel.get('username'):
            message_text += f"Username: @{channel['username']}\n"
        message_text += f"\nКлючевые слова:\n{', '.join(channel.get('keywords', []))}"

        await send_message(callback.message.chat.id, message_text, reply_markup=get_channel_info_keyboard(chat_id))


@dp.callback_query(F.data == "add")
async def add_channel(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(BotStates.waiting_for_forward)
    keyboard = [[InlineKeyboardButton(text="🔙 Назад", callback_data="back")]]
    await send_message(callback.message.chat.id, "Перешлите сообщение из чата, который хотите добавить в мониторинг",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))


@dp.message(BotStates.waiting_for_forward)
async def handle_forwarded_message(message: types.Message, state: FSMContext):
    if message.forward_from_chat or message.forward_from:
        if message.forward_from_chat:
            chat_id = message.forward_from_chat.id
            chat_type = message.forward_from_chat.type
            title = message.forward_from_chat.title
            username = message.forward_from_chat.username
        else:
            chat_id = message.forward_from.id
            chat_type = "user" if not message.forward_from.is_bot else "bot"
            title = message.forward_from.first_name
            if message.forward_from.last_name:
                title += f" {message.forward_from.last_name}"
            username = message.forward_from.username

        chat_data = {'chat_id': chat_id, 'type': chat_type, 'title': title, 'username': username, 'keywords': []}

        existing_chat = channels_collection.find_one({'chat_id': chat_id})
        if existing_chat:
            await send_message(message.chat.id, f"Чат {title} уже добавлен в мониторинг!",
                reply_markup=get_main_menu_keyboard())
            await state.clear()
            return

        channels_collection.insert_one(chat_data)
        await state.set_state(BotStates.waiting_keywords)
        await state.update_data(chat_id=chat_id)

        await send_message(message.chat.id, f"Чат {title} ({chat_type}) успешно добавлен в мониторинг!\n"
                                            "Теперь отправьте ключевые слова через запятую:",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="back")]]))
    else:
        await send_message(message.chat.id, "Пожалуйста, перешлите сообщение из чата или от пользователя/бота",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="back")]]))


@dp.message(BotStates.waiting_keywords)
async def handle_keywords(message: types.Message, state: FSMContext):
    data = await state.get_data()
    chat_id = data['chat_id']
    keywords = [kw.strip() for kw in message.text.split(',')]

    channels_collection.update_one({'chat_id': chat_id}, {'$set': {'keywords': keywords}})

    channel = channels_collection.find_one({'chat_id': chat_id})
    await send_message(message.chat.id, f"Ключевые слова для чата {channel['title']} успешно обновлены!",
        reply_markup=get_main_menu_keyboard())
    await state.clear()


@dp.callback_query(F.data.startswith("set_keywords_"))
async def set_keywords(callback: types.CallbackQuery, state: FSMContext):
    chat_id = int(callback.data.split('_')[2])
    channel = channels_collection.find_one({'chat_id': chat_id})
    if channel:
        await state.set_state(BotStates.waiting_keywords)
        await state.update_data(chat_id=chat_id)
        await send_message(callback.message.chat.id, f"Текущие ключевые слова для чата {channel['title']}:\n"
                                                     f"{', '.join(channel.get('keywords', []))}\n\n"
                                                     "Отправьте новые ключевые слова через запятую:",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data=f"channel_info_{chat_id}")]]))


@dp.callback_query(F.data.startswith("confirm_delete_"))
async def confirm_delete(callback: types.CallbackQuery):
    chat_id = int(callback.data.split('_')[2])
    channel = channels_collection.find_one({'chat_id': chat_id})
    if channel:
        keyboard = [[InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"do_delete_{chat_id}")],
            [InlineKeyboardButton(text="❌ Нет, отмена", callback_data=f"channel_info_{chat_id}")]]
        await send_message(callback.message.chat.id, f"Вы уверены, что хотите удалить чат {channel['title']}?",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))


@dp.callback_query(F.data.startswith("do_delete_"))
async def do_delete(callback: types.CallbackQuery):
    chat_id = int(callback.data.split('_')[2])
    channel = channels_collection.find_one({'chat_id': chat_id})
    if channel:
        channels_collection.delete_one({'chat_id': chat_id})
        await send_message(callback.message.chat.id, f"Чат {channel['title']} удален из мониторинга",
            reply_markup=get_main_menu_keyboard())


@dp.callback_query(F.data == "back")
async def back_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await send_message(callback.message.chat.id, "Выберите чат для управления:", reply_markup=get_main_menu_keyboard())


async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
