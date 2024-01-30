from logging import Logger

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio.engine import AsyncConnection
from sqlalchemy import select

from lib.models import Base, Users, Films


class Postgres:
    def __init__(self, url, logger: Logger):
        self.url = url
        self.logger = logger

        self.engine = create_async_engine(self.url, echo=False)
        self.async_session = async_sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)

    async def __scalar(self, statement):
        async with self.async_session() as session:
            return await session.scalar(statement)

    async def insert(self, model):
        async with self.async_session() as session:
            async with session.begin():
                session.add(model)

    async def delete(self, model):
        async with self.async_session() as session:
            async with session.begin():
                await session.delete(model)

    async def get_user(self, user_id: int):
        stmt = select(Users.user_id).where(Users.user_id == user_id)
        return await self.__scalar(stmt)

    async def get_admin(self, user_id: int):
        stmt = select(Users.is_admin).where(Users.user_id == user_id)
        return await self.__scalar(stmt)

    async def get_film(self, code: int, obj=False):
        if obj:
            stmt = select(Films).where(Films.code == code)
        else:
            stmt = select(Films.title).where(Films.code == code)
        return await self.__scalar(stmt)

    async def delete_film(self, film: Films):
        await self.delete(film)

    async def create_tables(self):
        self.logger.info('Create tables')
        async with self.engine.begin() as conn:  # type: AsyncConnection
            await conn.run_sync(Base.metadata.create_all)

    async def drop_tables(self):
        self.logger.info('Drop tables')
        async with self.engine.begin() as conn:  # type: AsyncConnection
            await conn.run_sync(Base.metadata.drop_all)
