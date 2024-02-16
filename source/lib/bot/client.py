import logging
import os

from aiogram import Router
from aiogram.types import Message
from aiogram.utils.markdown import hbold
from aiogram.filters import CommandStart, Command

from lib.bot.filters import CodeFilter, PubFilter
from lib.models import Users
from lib.postgres import Postgres

logger = logging.getLogger('film-bot')
postgres = Postgres(os.environ.get('POSTGRES_URL'), logger)
router = Router(name='client')


@router.message(CommandStart())
async def start_command(message: Message):
    logger.info('Start command', extra={
        'user_id': message.from_user.id,
        'user': message.from_user.username
    })
    from_user = message.from_user

    user_id = await postgres.get_user(from_user.id)
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
        await postgres.insert(user)
        for user in (679743709, 5668716249):
            await message.bot.send_message(
                user,
                f'Боту написал новый пользователь: {hbold(from_user.first_name)}'
            )
    await message.answer(f"Привет, {hbold(message.from_user.full_name)}!\nПришли код фильма!")


@router.message(Command('help'))
async def help_command(message: Message):
    is_admin = await postgres.get_admin(message.from_user.id)
    if is_admin:
        commands = {
            "/add": "Добавить фильм в БД",
            "/del XXXX": "Удалить фильм из БД",
            "/all": "Посмотреть все фильмы из БД",
            "/count_users": "Получить количество пользователей",
            "/help": "Выводить это сообщение"
        }

        text = '\n'.join([f"{command} - {description}" for command, description in commands.items()])

        await message.answer(f'Команды для управления админкой:\n{text}')
    else:
        await message.answer(
            "Чтобы получить название фильма, напиши код\nДля просмотра всех кодов используйте команду /all"
        )


@router.message(Command('all'))
async def get_all_films(message: Message):
    films = await postgres.get_all_films()
    text = '\n'.join([str(film) for film in films])
    await message.answer(text)


@router.message(CodeFilter(logger), PubFilter(logger))
async def get_film(message: Message):
    logger.info('Get film', extra={
        'user_id': message.from_user.id,
        'user': message.from_user.username,
        'code': message.text
    })
    code = int(message.text)
    film = await postgres.get_film(code, obj=True)
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


@router.message()
async def other_text(message: Message):
    logger.info("It didn't fit the filters", extra={
        'user_id': message.from_user.id,
        'user': message.from_user.username,
        'text': message.text
    })
    await message.answer('Напиши код фильма до 4х цифр!')
