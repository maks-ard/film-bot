import logging
import os
from typing import Any

from aiogram import Router, F
from aiogram.filters import Command
from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import ReplyKeyboardRemove

from lib.bot.filters import AdminFilter, CodeFilter
from lib.bot.keyboards import yes_no_keyboard, yes_no_cancel_keyboard, AnswerCallback, cancel_keyboard
from lib.models import Films
from lib.postgres import Postgres


class Film(StatesGroup):
    code = State()
    title = State()
    add_description = State()
    description = State()
    add_links_view = State()
    links_view = State()
    add_source_url = State()
    source_url = State()


logger = logging.getLogger('film-bot')
postgres = Postgres(os.environ.get('POSTGRES_URL'), logger)
router = Router(name='admin')
admin_filter = AdminFilter(postgres, logger)


@router.message(Command('add'), admin_filter)
async def add_film(message: types.Message, state: FSMContext):
    await state.set_state(Film.code)
    await message.answer('Введи код фильма', reply_markup=cancel_keyboard())


@router.message(Command('all'), admin_filter)
async def get_all_films(message: types.Message):
    films = await postgres.get_all_films()
    text = '\n'.join([str(film) for film in films])
    await message.answer(text)


@router.message(Command('del'), admin_filter)
async def delete_film(message: types.Message):
    logger.info('Try delete film', extra={
        'user_id': message.from_user.id,
        'user': message.from_user.username
    })

    try:
        _, code = message.text.split(' ')
        film = await postgres.get_film(int(code), obj=True)
        if film is None:
            await message.answer(f"Фильм с кодом {code} не найден")
            return
        title = film.title
        await postgres.delete_film(film)
        await message.answer(f"Фильм {title} удалён")

    except ValueError:
        await message.answer('Некоректный формат!\nВведи в формате /del 1234')
    except Exception as ex:
        await message.answer('Непредвиденная ошибка удаления фильма!')
        logger.error(ex)


@router.callback_query(AnswerCallback.filter(F.answer == 'cancel'))
async def cancel_handler(query: types.CallbackQuery, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is None:
        return

    logger.info("Cancelling state %r", current_state)

    await state.clear()
    await query.message.edit_text("Добавление фильма отменено")


@router.message(Film.code, CodeFilter(logger))
async def add_code(message: types.Message, state: FSMContext):
    title = await postgres.get_film(int(message.text))
    if title:
        await message.answer(f'Фильм с кодом {message.text} уже есть в бд')
        return
    await state.update_data(code=message.text)
    await state.set_state(Film.title)
    await message.answer('Введи название фильма', reply_markup=cancel_keyboard())


@router.message(Film.title)
async def add_title(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(Film.add_description)
    await message.answer('Добавить описание?', reply_markup=yes_no_cancel_keyboard())


@router.callback_query(Film.add_description, AnswerCallback.filter(F.answer == 'yes'))
async def yes_description(query: types.CallbackQuery, state: FSMContext):
    await state.set_state(Film.description)
    await query.message.edit_text('Введи описание')


@router.message(Film.description)
async def add_description(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(Film.add_source_url)
    await message.answer('Добавить ссылку reels/shorts?', reply_markup=yes_no_cancel_keyboard())


@router.callback_query(Film.add_description, AnswerCallback.filter(F.answer == 'no'))
async def no_description(query: types.CallbackQuery, state: FSMContext):
    await state.set_state(Film.add_source_url)
    await query.message.edit_text('Добавить ссылку reels/shorts?', reply_markup=yes_no_cancel_keyboard())


@router.callback_query(Film.add_source_url, AnswerCallback.filter(F.answer == 'yes'))
async def yes_source_url(query: types.CallbackQuery, state: FSMContext):
    await state.set_state(Film.source_url)
    await query.message.edit_text('Введи ссылку reels/shorts')


@router.message(Film.source_url)
async def add_source_url(message: types.Message, state: FSMContext):
    await state.update_data(source_url=message.text)
    await state.set_state(Film.add_links_view)
    await message.answer('Добавить ссылки для просмотра?', reply_markup=yes_no_cancel_keyboard())


@router.callback_query(Film.add_source_url, AnswerCallback.filter(F.answer == 'no'))
async def no_source_url(query: types.CallbackQuery, state: FSMContext):
    await state.get_data()
    await state.set_state(Film.add_links_view)
    await query.message.edit_text('Добавить ссылки для просмотра?', reply_markup=yes_no_cancel_keyboard())


@router.callback_query(Film.add_links_view, AnswerCallback.filter(F.answer == 'yes'))
async def yes_links_view(query: types.CallbackQuery, state: FSMContext):
    await state.set_state(Film.links_view)
    await query.message.edit_text('Введи ссылки на просмотр через пробел')


@router.message(Film.links_view)
async def add_links_view(message: types.Message, state: FSMContext):
    data = await state.update_data(links=message.text.split(' '))
    await state.clear()
    text = await add_data(message, data)
    await message.answer(text)


@router.callback_query(Film.add_links_view, AnswerCallback.filter(F.answer == 'no'))
async def no_links_view(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.clear()
    text = await add_data(query, data)
    await query.message.edit_text(text)


async def add_data(callback: types.Message | types.CallbackQuery, data: dict[str, Any]) -> str:
    film = Films(
        code=int(data['code']),
        title=data['title'],
        description=data.get('description'),
        source_url=data.get('source_url'),
        links_view=data.get('links_view')
    )

    await postgres.insert(film)
    text = 'Фильм добавлен\n'
    text += f'Код: {film.code}\n'
    text += f'Название: {film.title}\n'
    if film.description:
        text += f'Описание: {film.description}\n'
    if film.links_view:
        text += f'Ссылки для просмотра: {", ".join(film.links_view)}\n'
    if film.source_url:
        text += f'Ссылка shorts/reels: {film.source_url}\n'

    return text
