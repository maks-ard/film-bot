from logging import Logger

from aiogram import Router
from aiogram.filters import Filter
from aiogram.types import Message
from aiogram.types.chat_member_left import ChatMemberLeft
from aiogram.types.chat_member_member import ChatMemberMember

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
        user_channel_status_movienightee = await message.bot.get_chat_member(
            chat_id='@movienightee',
            user_id=message.from_user.id
        )

        if isinstance(user_channel_status_movienightee, ChatMemberMember):
            return True
        await message.answer(
            'Для получения фильма нужно быть подписанным на @movienightee'
        )
        return False
