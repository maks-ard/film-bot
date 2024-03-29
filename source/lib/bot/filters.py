from logging import Logger

from aiogram import Router
from aiogram.filters import Filter
from aiogram.types import Message
from aiogram.types.chat_member_member import ChatMemberMember
from aiogram.types.chat_member_administrator import ChatMemberAdministrator
from aiogram.types.chat_member_owner import ChatMemberOwner

from lib.bot.keyboards import pubs_inline_keyboard
from lib.postgres import Postgres

router = Router()


class AdminFilter(Filter):
    def __init__(self, postgres: Postgres, logger: Logger) -> None:
        self.logger = logger
        self.postgres = postgres

    async def __call__(self, message: Message) -> bool:
        is_admin = await self.postgres.get_admin(message.from_user.id)
        if not is_admin:
            self.logger.warning('An attempt to use the admin panel without rights', extra={
                'user_id': message.from_user.id,
                'user': message.from_user.username,
                'is_admin': is_admin,
                'text': message.text
            })
            return False
        return True


class CodeFilter(Filter):
    def __init__(self, logger: Logger) -> None:
        self.logger = logger

    async def __call__(self, message: Message) -> bool:
        is_digit = message.text.isdigit()
        self.logger.debug(f'Message {message.text} is number: {is_digit}')
        return is_digit and len(message.text) < 5


class PubFilter(Filter):
    def __init__(self, logger: Logger) -> None:
        self.logger = logger

    async def __call__(self, message: Message) -> bool:
        channels = [
            {
                "name": "Фильмы | Сериалы | Мультфильмы",
                "url": "https://t.me/movienightee",
                "chat_id": "@movienightee"
            },
            {
                "name": "ВБ МАНИЯ",
                "url": "https://t.me/WildBMania",
                "chat_id": "@WildBMania"
            }
        ]

        keyboard = pubs_inline_keyboard(channels)

        for channel in channels:
            user_channel_status = await message.bot.get_chat_member(
                chat_id=channel.get('chat_id'),
                user_id=message.from_user.id
            )

            if not isinstance(user_channel_status, (ChatMemberMember, ChatMemberAdministrator, ChatMemberOwner)):
                await message.answer(
                    'Для пользования ботом нужно быть подписанным на каналы:',
                    reply_markup=keyboard
                )
                return False
        return True




