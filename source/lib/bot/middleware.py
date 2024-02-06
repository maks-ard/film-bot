from logging import Logger
from typing import Callable, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message


class LogMessageMiddleware(BaseMiddleware):
    def __init__(self, logger: Logger) -> None:
        self.logger = logger

    async def __call__(
            self,
            handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: dict[str, Any]
    ) -> Any:
        self.logger.info(event.text, extra={
            'username': event.from_user.username,
            'user_id': event.from_user.id
        })

        return await handler(event, data)
