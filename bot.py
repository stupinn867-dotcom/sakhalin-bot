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

# Состояния для сбора данных
class OrderState(StatesGroup):
    waiting_for_data = State()

# --- ГЛАВНОЕ МЕНЮ ---
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

# --- ЗАПРОС ДАННЫХ ПО УСЛУГАМ ---
@dp.callback_query(F.data.startswith("service_"))
async def service_handler(callback: types.CallbackQuery, state: FSMContext):
    service = callback.data.split("_")[1]
    await state.update_data(service_name=service)
    
    text = "Напишите ваш адрес, время и номер телефона."
    if service == "posylka":
        text = "Отлично! Напишите, пожалуйста: 1. Название ПВЗ (Ozon/WB и др.), 2. Код получения, 3. Адрес доставки, 4. Время, 5. Телефон."
    elif service == "produkty":
        text = "Отлично! Напишите список продуктов, адрес доставки, время и телефон. (Оплата по чеку)."
    elif service == "muzh":
        text = "Отлично! Напишите, что нужно сделать, ваш адрес, время и телефон."
    elif service == "voditel":
        text = "Отлично! Напишите откуда и куда везти, марку авто, время и телефон."
    elif service == "soprovozhdenie":
        text = "Отлично! Напишите куда сопроводить, откуда забрать, время и телефон."

    await callback.message.answer(text + "\n\n(Нажмите /start, чтобы отменить)")
    await state.set_state(OrderState.waiting_for_data)
    await callback.answer()

# --- СОХРАНЕНИЕ ЗАЯВКИ И ОТПРАВКА ТЕБЕ ---
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

# --- МИНИ-СЕРВЕР ---
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
