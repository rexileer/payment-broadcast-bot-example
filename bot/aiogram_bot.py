import os
from aiogram import Bot
from aiogram.client.bot import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession

TOKEN = os.getenv('TELEGRAM_TOKEN')
session = AiohttpSession()
bot = Bot(token=TOKEN, session=session, default=DefaultBotProperties(parse_mode='HTML')) 