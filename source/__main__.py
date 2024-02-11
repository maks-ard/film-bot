from dotenv import load_dotenv

load_dotenv()

import argparse
import asyncio
import logging
import sys
from os import getenv

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from pythonjsonlogger import jsonlogger

from lib.bot.middleware import LogMessageMiddleware
from lib.postgres import Postgres
from lib.bot.admin import router as admin_router
from lib.bot.client import router as client_router


class Service:
    def __init__(self, logger: logging.Logger, args):
        self.logger = logger
        self.postgres = Postgres(args.postgres_url, self.logger)
        self.dp = Dispatcher()
        self.bot = Bot(args.token, parse_mode=ParseMode.HTML)

    async def start(self):
        self.logger.info('Start')
        # await self.postgres.drop_tables()
        # await self.postgres.create_tables()

        self.dp.message.outer_middleware.register(LogMessageMiddleware(self.logger))
        self.dp.include_router(admin_router)
        self.dp.include_router(client_router)

        self.logger.info('Start polling')
        await self.dp.start_polling(self.bot, logger=self.logger)


def _get_logger(level: int) -> logging.Logger:
    class LogFilter(logging.Filter):
        def filter(self, record):
            record.service = 'film-bot'
            return True

    log = logging.getLogger('film-bot')
    log.setLevel(level * 10)

    stream_handler = logging.StreamHandler(sys.stdout)

    log_format = "%(levelname)-8s %(filename)s %(asctime)s %(lineno)d %(message)s"
    formatter = jsonlogger.JsonFormatter(
        fmt=log_format, json_ensure_ascii=False
    )

    stream_handler.setFormatter(formatter)

    log.addHandler(stream_handler)
    log.addFilter(LogFilter())

    return log


def _parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--postgres_url',
        default=getenv('POSTGRES_URL')
    )

    parser.add_argument(
        '--token',
        default=getenv('TOKEN')
    )

    parser.add_argument(
        '--loglevel',
        default=2,
        type=int
    )

    return parser


if __name__ == "__main__":
    _args = _parse_args().parse_args()
    _logger = _get_logger(_args.loglevel)

    service = Service(_logger, _args)

    try:
        asyncio.run(service.start())

    except KeyboardInterrupt:
        _logger.info('Force stopping')

    except Exception as ex:
        _logger.critical('Critical error', extra={
            'ex': ex
        })
