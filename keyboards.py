from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton 
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

contact = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Поделиться контактом', request_contact=True)]
    ],
    resize_keyboard=True
    )

main = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='📋Пройти верификацию', callback_data='verif')]
    ])