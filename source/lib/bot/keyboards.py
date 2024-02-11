from aiogram.filters.callback_data import CallbackData
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


class AnswerCallback(CallbackData, prefix='admin'):
    answer: str


yes_no_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Да"),
            KeyboardButton(text="Нет"),
        ]
    ],
    resize_keyboard=True,
)


def pubs_inline_keyboard(channels: list[dict]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for channel in channels:
        builder.button(text=channel['name'], url=channel['url'])

    builder.adjust(1)

    return builder.as_markup()


def yes_no_cancel_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text='Да', callback_data=AnswerCallback(answer='yes').pack()),
        InlineKeyboardButton(text='Нет', callback_data=AnswerCallback(answer='no').pack())
    )

    builder.row(InlineKeyboardButton(text='Отмена', callback_data=AnswerCallback(answer='cancel').pack()))
    return builder.as_markup()


def cancel_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text='Отмена', callback_data=AnswerCallback(answer='cancel').pack())
    return builder.as_markup()
