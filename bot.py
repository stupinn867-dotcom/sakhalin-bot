import asyncio
import logging
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = os.environ.get("ADMIN_ID")

bot = Bot(token=TOKEN)
dp = Dispatcher()

class OrderState(StatesGroup):
    waiting_for_data = State()

def get_main_menu():
    kb = [
        [InlineKeyboardButton(text="ℹ️ Цены и условия", callback_data="info")],
        [InlineKeyboardButton(text="🚚 Забрать посылку", callback_data="service_posylka")],
        [InlineKeyboardButton(text="🛒 Доставка продуктов", callback_data="service_produkty")],
        [InlineKeyboardButton(text="🔧 Муж на час", callback_data="service_muzh")],
        [InlineKeyboardButton(text="🚗 Трезвый водитель", callback_data="service_voditel")],
        [InlineKeyboardButton(text="👴 Сопровождение", callback_data="service_soprovozhdenie")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("Здравствуйте! Рады видеть вас в сервисе «Помощник 65» 🙌\nВыберите нужную услугу:", reply_markup=get_main_menu())

@dp.callback_query(F.data == "info")
async def info_handler(callback: types.CallbackQuery):
    text = ("*Наши цены:*\n"
            "🚚 Посылка — от 600 ₽\n"
            "🛒 Продукты — от 800 ₽ + чек\n"
            "🔧 Муж на час — от 1500 ₽\n"
            "🚗 Водитель — от 2000 ₽\n"
            "👴 Сопровождение — от 1500 ₽\n"
            "*(Точная стоимость зависит от адреса и сложности).*\n\n"
            "*Правила работы:*\n"
            "• Оплата по факту (наличные/перевод).\n"
            "• Вы обязаны проверить товар при курьере.\n"
            "• Если отказываетесь от продуктов — оплачиваете чек и выезд.\n"
            "• Если посылка повреждена на ПВЗ — курьер пришлет фото, и вы решите, забирать ли её.")
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🏠 В меню", callback_data="back")]])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data == "back")
async def back_handler(callback: types.CallbackQuery):
    await callback.message.edit_text("Выберите нужную услугу:", reply_markup=get_main_menu())

@dp.callback_query(F.data.startswith("service_"))
async def service_handler(callback: types.CallbackQuery, state: FSMContext):
    service = callback.data.split("_")[1]
    await state.update_data(service_name=service)
    
    text = "Напишите ваш адрес, время и номер телефона."
    if service == "posylka":
        text = "Отлично! 📦 Напишите, пожалуйста:\n1. Название ПВЗ (Ozon, WB, СДЭК и др.)\n2. Код получения или QR\n3. Адрес доставки\n4. К какому времени привезти\n5. Ваш номер телефона"
    elif service == "produkty":
        text = "Отлично! 🛒 Напишите, пожалуйста:\n1. Список продуктов (или фото)\n2. Адрес доставки\n3. К какому времени\n4. Ваш номер телефона\n_(Оплата: чек + 800 руб.)_"
    elif service == "muzh":
        text = "Отлично! 🔧 Напишите, пожалуйста:\n1. Что нужно сделать\n2. Есть ли свои материалы/инструменты\n3. Адрес\n4. Удобное время\n5. Ваш номер телефона"
    elif service == "voditel":
        text = "Отлично! 🚗 Напишите, пожалуйста:\n1. Откуда и куда везти\n2. Марку и цвет авто\n3. На какое время\n4. Ваш номер телефона"
    elif service == "soprovozhdenie":
        text = "Отлично! 👴 Напишите, пожалуйста:\n1. Куда сопроводить (врач, магазин, МФЦ)\n2. Откуда забрать\n3. Кого сопроводить\n4. Удобное время\n5. Ваш номер телефона"

    await callback.message.answer(text + "\n\n_(Нажмите /start, чтобы отменить)_", parse_mode="Markdown")
    await state.set_state(OrderState.waiting_for_data)
    await callback.answer()

@dp.message(OrderState.waiting_for_data)
async def process_order_data(message: types.Message, state: FSMContext):
    data = await state.get_data()
    service = data.get("service_name")
    
    names = {"posylka": "🚚 Забрать посылку", "produkty": "🛒 Доставка продуктов", "muzh": "🔧 Муж на час", "voditel": "🚗 Трезвый водитель", "soprovozhdenie": "👴 Сопровождение"}
    service_name = names.get(service, service)
    
    admin_text = (f"🚨 НОВЫЙ ЗАКАЗ!\n\n"
                  f"Услуга: {service_name}\n"
                  f"Данные: {message.text}\n"
                  f"Клиент: @{message.from_user.username} (id: {message.from_user.id})")
                  
    try:
        await bot.send_message(ADMIN_ID, admin_text)
    except Exception as e:
        logging.error(f"Ошибка отправки админу: {e}")

    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🏠 В меню", callback_data="back")]])
    await message.answer("✅ Спасибо! Ваша заявка принята. Наш оператор свяжется с вами в ближайшее время!", reply_markup=kb)
    await state.clear()

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
