from logging import Logger
from typing import Callable, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message


class LogMessageMiddleware(BaseMiddleware):
    def __init__(self, logger: Logger) -> None:
        self.logger = logger
        self.chat_id = -4192391002

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
        try:
            if event.chat.id != self.chat_id:
                await event.bot.send_message(self.chat_id, f"{event.from_user.first_name}: {event.text}")
        except:
            self.logger.error('Error forward message', extra={
                "type_event": type(event),
                "event": str(event)
            })

        return await handler(event, data)
