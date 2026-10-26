import asyncio
import logging
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = os.environ.get("BOT_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- ГЛАВНОЕ МЕНЮ ---
def get_main_menu():
    kb = [
        [InlineKeyboardButton(text="ℹ️ Цены и условия", callback_data="info")],
        [InlineKeyboardButton(text="🚚 Забрать посылку", callback_data="posylka")],
        [InlineKeyboardButton(text="🛒 Доставка продуктов", callback_data="produkty")],
        [InlineKeyboardButton(text="🔧 Муж на час", callback_data="muzh")],
        [InlineKeyboardButton(text="🚗 Трезвый водитель", callback_data="voditel")],
        [InlineKeyboardButton(text="👴 Сопровождение", callback_data="soprovozhdenie")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("Привет! Я бот-помощник в Южно-Сахалинске. Выберите нужную услугу:", reply_markup=get_main_menu())

# --- ОБРАБОТКА КНОПОК ---
@dp.callback_query(F.data == "info")
async def info_handler(callback: types.CallbackQuery):
    text = ("Наши цены:\n"
            "🚚 Посылка — от 600 ₽\n"
            "🛒 Продукты — от 800 ₽ + чек\n"
            "🔧 Муж на час — от 1500 ₽\n"
            "🚗 Водитель — от 2000 ₽\n"
            "👴 Сопровождение — от 1500 ₽\n\n"
            "Оплата после выполнения. Возврат продуктов невозможен.")
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🏠 В меню", callback_data="back")]])
    await callback.message.edit_text(text, reply_markup=kb)

@dp.callback_query(F.data == "back")
async def back_handler(callback: types.CallbackQuery):
    await callback.message.edit_text("Выберите нужную услугу:", reply_markup=get_main_menu())

# Заглушки для услуг (потом допишем логику)
@dp.callback_query(F.data.in_({"posylka", "produkty", "muzh", "voditel", "soprovozhdenie"}))
async def service_handler(callback: types.CallbackQuery):
    await callback.message.answer("Отлично! Напишите ваш адрес, время и номер телефона.")
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🏠 В меню", callback_data="back")]])
    await callback.message.answer("Или вернитесь в меню:", reply_markup=kb)
    await callback.answer()

# --- МИНИ-СЕРВЕР (чтобы хостинг не засыпал) ---
async def handle(request):
    return web.Response(text="Bot is running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

async def main():
    logging.basicConfig(level=logging.INFO)
    await start_web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
