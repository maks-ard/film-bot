from logging import Logger
from typing import Any

from aiogram import Router, F
from aiogram.filters import Command
from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import ReplyKeyboardRemove

from lib.bot.filters import AdminFilter, CodeFilter
from lib.bot.keyboards import yes_no_keyboard
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


class Admin:
    def __init__(self, postgres: Postgres, logger: Logger):
        self.logger = logger
        self.postgres = postgres

    async def add_film(self, message: types.Message, state: FSMContext):
        await state.set_state(Film.code)
        await message.answer('Введи код фильма')

    async def cancel_handler(self, message: types.Message, state: FSMContext) -> None:
        current_state = await state.get_state()
        if current_state is None:
            return

        self.logger.info("Cancelling state %r", current_state)

        await state.clear()
        await message.answer(
            "Cancelled.",
            reply_markup=ReplyKeyboardRemove(),
        )

    async def add_code(self, message: types.Message, state: FSMContext):
        title = await self.postgres.get_film(int(message.text))
        if title:
            await message.answer(f'Фильм с кодом {message.text} уже есть в бд')
            return
        await state.update_data(code=message.text)
        await state.set_state(Film.title)
        await message.answer('Введи название фильма')

    async def add_title(self, message: types.Message, state: FSMContext):
        await state.update_data(title=message.text)
        await state.set_state(Film.add_description)
        await message.answer('Добавить описание?', reply_markup=yes_no_keyboard)

    async def yes_description(self, message: types.Message, state: FSMContext):
        await state.set_state(Film.description)
        await message.answer('Введи описание')

    async def add_description(self, message: types.Message, state: FSMContext):
        await state.update_data(description=message.text)
        await state.set_state(Film.add_source_url)
        await message.answer('Добавить ссылку reels/shorts?', reply_markup=yes_no_keyboard)

    async def no_description(self, message: types.Message, state: FSMContext):
        await state.set_state(Film.add_source_url)
        await message.answer('Добавить ссылку reels/shorts?', reply_markup=yes_no_keyboard)

    async def yes_source_url(self, message: types.Message, state: FSMContext):
        await state.set_state(Film.source_url)
        await message.answer('Введи ссылку reels/shorts')

    async def add_source_url(self, message: types.Message, state: FSMContext):
        await state.update_data(source_url=message.text)
        await state.set_state(Film.add_links_view)
        await message.answer('Добавить ссылки для просмотра?', reply_markup=yes_no_keyboard)

    async def no_source_url(self, message: types.Message, state: FSMContext):
        await state.get_data()
        await state.set_state(Film.add_links_view)
        await message.answer('Добавить ссылки для просмотра?', reply_markup=yes_no_keyboard)

    async def yes_links_view(self, message: types.Message, state: FSMContext):
        await state.set_state(Film.links_view)
        await message.answer('Введи ссылки на просмотр через пробел')

    async def add_links_view(self, message: types.Message, state: FSMContext):
        data = await state.update_data(links=message.text.split(' '))
        await state.clear()
        await self.add_data(message, data)

    async def no_links_view(self, message: types.Message, state: FSMContext):
        data = await state.get_data()
        await state.clear()
        await self.add_data(message, data)

    async def add_data(self, message: types.Message, data: dict[str, Any]) -> None:
        film = Films(
            code=int(data['code']),
            title=data['title'],
            description=data.get('description'),
            source_url=data.get('source_url'),
            links_view=data.get('links_view')
        )

        await self.postgres.insert(film)
        text = 'Фильм добавлен\n'
        text += f'Код: {film.code}\n'
        text += f'Название: {film.title}\n'
        if film.description:
            text += f'Описание: {film.description}\n'
        if film.links_view:
            text += f'Ссылки для просмотра: {", ".join(film.links_view)}\n'
        if film.source_url:
            text += f'Ссылка shorts/reels: {film.source_url}\n'

        await message.answer(text, reply_markup=ReplyKeyboardRemove())

    async def delete_film(self, message: types.Message):
        self.logger.info('Try delete film', extra={
            'user_id': message.from_user.id,
            'user': message.from_user.username
        })

        try:
            _, code = message.text.split(' ')
            film = await self.postgres.get_film(int(code), obj=True)
            if film is None:
                await message.answer(f"Фильм с кодом {code} не найден")
                return
            title = film.title
            await self.postgres.delete_film(film)
            await message.answer(f"Фильм {title} удалён")

        except ValueError:
            await message.answer('Некоректный формат!\nВведи в формате /del 1234')
        except Exception as ex:
            await message.answer('Непредвиденная ошибка удаления фильма!')
            self.logger.error(ex)

    def register(self):
        router = Router(name='admin')
        self.logger.info('Register router Client')

        admin_filter = AdminFilter(self.postgres, self.logger)
        router.message.filter(admin_filter)
        router.message.register(self.add_film, Command('add'), admin_filter)
        router.message.register(self.delete_film, Command('del'), admin_filter)
        router.message.register(self.cancel_handler, Command('cancel'), F.text.casefold() == "cancel")
        router.message.register(self.add_code, Film.code, CodeFilter(self.logger))
        router.message.register(self.add_title, Film.title)
        router.message.register(self.yes_description, Film.add_description, F.text.casefold() == 'да')
        router.message.register(self.add_description, Film.description)
        router.message.register(self.no_description, Film.add_description, F.text.casefold() == 'нет')
        router.message.register(self.yes_links_view, Film.add_links_view, F.text.casefold() == 'да')
        router.message.register(self.add_links_view, Film.links_view)
        router.message.register(self.no_links_view, Film.add_links_view, F.text.casefold() == 'нет')
        router.message.register(self.yes_source_url, Film.add_source_url, F.text.casefold() == 'да')
        router.message.register(self.add_source_url, Film.source_url)
        router.message.register(self.no_source_url, Film.add_source_url, F.text.casefold() == 'нет')

        return router
