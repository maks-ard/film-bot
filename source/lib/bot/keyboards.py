from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

yes_no_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Да"),
            KeyboardButton(text="Нет"),
        ]
    ],
    resize_keyboard=True,
)
