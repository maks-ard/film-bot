from logging import Logger

from aiogram import Router
from aiogram.types import Message
from aiogram.utils.markdown import hbold
from aiogram.filters import CommandStart

from lib.bot.filters import CodeFilter, AdminFilter, PubFilter
from lib.models import Users
from lib.postgres import Postgres


class Client:
    def __init__(self, postgres: Postgres, logger: Logger):
        self.logger = logger
        self.postgres = postgres

    async def start_command(self, message: Message):
        self.logger.info('Start command', extra={
            'user_id': message.from_user.id,
            'user': message.from_user.username
        })
        from_user = message.from_user

        user_id = await self.postgres.get_user(from_user.id)
        if user_id is None:
            if from_user.username in ('maks_ard', 'quemarstu'):
                is_admin = True
            else:
                is_admin = False

            user = Users(
                user_id=from_user.id,
                is_bot=from_user.is_bot,
                first_name=from_user.first_name,
                last_name=from_user.last_name,
                username=from_user.username,
                language_code=from_user.language_code,
                is_premium=from_user.is_premium,
                is_admin=is_admin
            )
            await self.postgres.insert(user)
            await message.bot.send_message(
                5668716249,
                f'Боту написал новый пользователь: {hbold(from_user.username)}'
            )
        await message.answer(f"Привет, {hbold(message.from_user.full_name)}!\nПришли код фильма!")

    async def get_film(self, message: Message):
        self.logger.info('Get film', extra={
            'user_id': message.from_user.id,
            'user': message.from_user.username,
            'code': message.text
        })
        code = int(message.text)
        film = await self.postgres.get_film(code, obj=True)
        if film is None:
            await message.answer(f"Фильм с кодом {code} не найден!")
        else:
            text = f'Название: {film.title}\n'
            if film.description:
                text += f'Описание: {film.description}\n'
            if film.links_view:
                text += f'Ссылки для просмотра: {", ".join(film.links_view)}\n'
            if film.source_url:
                text += f'Ссылка shorts/reals: {film.source_url}\n'
            await message.answer(text)

    async def other_text(self, message: Message):
        self.logger.info("It didn't fit the filters", extra={
            'user_id': message.from_user.id,
            'user': message.from_user.username,
            'text': message.text
        })
        await message.answer('Напиши код фильма из 4х цифр')

    def register(self):
        self.logger.info('Register router Client')
        router = Router(name='client')

        router.message.register(self.start_command, CommandStart())
        router.message.register(self.get_film, CodeFilter(self.logger), PubFilter(self.logger))
        router.message.register(self.other_text)  # Be last!!!

        return router
