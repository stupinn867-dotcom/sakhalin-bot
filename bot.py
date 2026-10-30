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
    waiting_for_review = State()
    waiting_for_complaint = State()
    waiting_for_waitlist = State()

def get_main_menu():
    kb = [
        [InlineKeyboardButton(text="ℹ️ Цены и условия", callback_data="info")],
        [InlineKeyboardButton(text="🚚 Забрать посылку", callback_data="service_posylka")],
        [InlineKeyboardButton(text="🛒 Доставка продуктов", callback_data="service_produkty")],
        [InlineKeyboardButton(text="🔧 Муж на час", callback_data="service_muzh")],
        [InlineKeyboardButton(text="🚗 Трезвый водитель", callback_data="service_voditel")],
        [InlineKeyboardButton(text="👴 Сопровождение", callback_data="service_soprovozhdenie")],
        [InlineKeyboardButton(text="🛠️ Другие услуги (скоро)", callback_data="future_services")],
        [InlineKeyboardButton(text="⭐ Отзывы и гарантии", callback_data="reviews")],
        [InlineKeyboardButton(text="🔄 Повторить заказ", callback_data="repeat_order")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("Здравствуйте! Рады видеть вас в сервисе «Помощник 65» 🙌\nВыберите нужную услугу:", reply_markup=get_main_menu())

@dp.callback_query(F.data == "info")
async def info_handler(callback: types.CallbackQuery):
    text = ("*Наши цены:*\n"
            "🚚 Забрать посылку — от 600 ₽\n"
            "🛒 Доставка продуктов — от 800 ₽ (плюс чек)\n"
            "🔧 Муж на час — от 1500 ₽\n"
            "🚗 Трезвый водитель — от 2000 ₽\n"
            "👴 Сопровождение — от 1500 ₽\n\n"
            "*(Точная стоимость зависит от адреса и сложности. Курьер согласует цену перед выездом).*\n\n"
            "*Правила работы:*\n"
            "• *Оплата:* по факту (наличные или перевод). Товары оплачиваются строго по чеку.\n"
            "• *Проверка:* осмотрите товар при курьере. После оплаты претензии по внешнему виду не принимаются.\n"
            "• *Отказ от продуктов:* оплачиваете чек и выезд. Возврат еды в магазин невозможен по закону.\n"
            "• *Поврежденные посылки:* если коробка помята на ПВЗ, курьер делает фото и спрашивает вас. За содержимое сервис не отвечает.\n"
            "• *Гарантия:* отвечаем за сохранность с момента получения в магазине/ПВЗ до передачи вам в руки.")
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Согласен", callback_data="back")],
        [InlineKeyboardButton(text="🏠 Вернуться в меню", callback_data="back")]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data == "reviews")
async def reviews_handler(callback: types.CallbackQuery):
    text = ("⭐ *Отзывы и гарантии*\n\n"
            "Мы молодая команда, но очень дорожим репутацией. Вот что говорят о нас первые клиенты:\n\n"
            "_(Здесь пока пусто, но скоро появятся скриншоты реальных отзывов)_")
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🏠 В меню", callback_data="back")]])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data == "future_services")
async def future_services_handler(callback: types.CallbackQuery):
    text = "🚀 *Мы постоянно развиваемся!* Какие услуги вы хотели бы у нас видеть? (Нажмите на кнопку, чтобы узнать подробности):"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🐕 Выгул собак", callback_data="wait_dog")],
        [InlineKeyboardButton(text="🧹 Клининг (уборка)", callback_data="wait_clean")],
        [InlineKeyboardButton(text="🍽️ Бронь столиков", callback_data="wait_table")],
        [InlineKeyboardButton(text="🏠 Вернуться в меню", callback_data="back")]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data.startswith("wait_"))
async def waitlist_handler(callback: types.CallbackQuery, state: FSMContext):
    service = callback.data.split("_")[1]
    names = {"dog": "Выгул собак", "clean": "Клининг", "table": "Бронь столиков"}
    s_name = names.get(service, service)
    
    await state.update_data(wait_service=s_name)
    text = f"Ого, вы не первый, кто спрашивает про *{s_name}*! 🙌\nМы как раз работаем над запуском. Оставьте ваш номер телефона, и мы напишем вам первыми, как только это появится (и дадим скидку 20% на первый заказ)!"
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🏠 В меню", callback_data="back")]])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await state.set_state(OrderState.waiting_for_waitlist)

@dp.message(OrderState.waiting_for_waitlist)
async def process_waitlist(message: types.Message, state: FSMContext):
    data = await state.get_data()
    service = data.get("wait_service")
    
    try:
        if str(message.from_user.id) != str(ADMIN_ID):
            await bot.send_message(ADMIN_ID, f"🔥 ЛИСТ ОЖИДАНИЯ\nУслуга: {service}\nТелефон: {message.text}\nКлиент: @{message.from_user.username}")
    except Exception as e:
        logging.error(f"Ошибка отправки: {e}")

    await message.answer("✅ Записали! Мы обязательно свяжемся с вами, как только запустим эту услугу.")
    await state.clear()

@dp.callback_query(F.data == "back")
async def back_handler(callback: types.CallbackQuery):
    await callback.message.edit_text("Выберите нужную услугу:", reply_markup=get_main_menu())

@dp.callback_query(F.data.startswith("service_"))
async def service_handler(callback: types.CallbackQuery, state: FSMContext):
    service = callback.data.split("_")[1]
    await state.update_data(service_name=service)
    
    text = "Напишите ваш адрес, время и номер телефона.\n\n_(Можете прикрепить геолокацию через скрепку 📎)_"
    if service == "posylka":
        text = "Отлично! 📦 Напишите, пожалуйста:\n1. Название ПВЗ (Ozon, WB, СДЭК и др.)\n2. Код получения или QR\n3. Адрес доставки (или геолокацию 📎)\n4. К какому времени привезти\n5. Ваш номер телефона"
    elif service == "produkty":
        text = "Отлично! 🛒 Напишите, пожалуйста:\n1. Список продуктов (или фото)\n2. Адрес доставки (или геолокацию 📎)\n3. К какому времени\n4. Ваш номер телефона\n_(Оплата: чек + 800 руб.)_"
    elif service == "muzh":
        text = "Отлично! 🔧 Напишите, пожалуйста:\n1. Что нужно сделать\n2. Есть ли свои материалы/инструменты\n3. Адрес (или геолокацию 📎)\n4. Удобное время\n5. Ваш номер телефона"
    elif service == "voditel":
        text = "Отлично! 🚗 Напишите, пожалуйста:\n1. Откуда и куда везти (или геолокацию 📎)\n2. Марку и цвет авто\n3. На какое время\n4. Ваш номер телефона"
    elif service == "soprovozhdenie":
        text = "Отлично! 👴 Напишите, пожалуйста:\n1. Куда сопроводить (врач, магазин, МФЦ)\n2. Откуда забрать (или геолокацию 📎)\n3. Кого сопроводить\n4. Удобное время\n5. Ваш номер телефона"

    await callback.message.answer(text + "\n\n_(Нажмите /start, чтобы отменить)_", parse_mode="Markdown")
    await state.set_state(OrderState.waiting_for_data)
    await callback.answer()

@dp.message(OrderState.waiting_for_data)
async def process_order_data(message: types.Message, state: FSMContext):
    data = await state.get_data()
    service = data.get("service_name")
    names = {"posylka": "🚚 Забрать посылку", "produkty": "🛒 Доставка продуктов", "muzh": "🔧 Муж на час", "voditel": "🚗 Трезвый водитель", "soprovozhdenie": "👴 Сопровождение"}
    service_name = names.get(service, service)
    
    if message.location:
        order_text = f"Геолокация: {message.location.latitude}, {message.location.longitude}"
    else:
        order_text = message.text
        
    await state.update_data(last_order=f"Услуга: {service_name}\nДанные: {order_text}")
    
    admin_text = (f"🚨 НОВЫЙ ЗАКАЗ!\n\nУслуга: {service_name}\nДанные: {order_text}\nКлиент: @{message.from_user.username}")
                  
    try:
        if str(message.from_user.id) != str(ADMIN_ID):
            await bot.send_message(ADMIN_ID, admin_text)
    except Exception as e:
        logging.error(f"Ошибка отправки админу: {e}")

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐ Оценить работу", callback_data="rate")],
        [InlineKeyboardButton(text="📝 Жалоба", callback_data="complaint")],
        [InlineKeyboardButton(text="🤝 Поделиться с другом", callback_data="share_bot")],
        [InlineKeyboardButton(text="🏠 В меню", callback_data="back")]
    ])
    await message.answer("✅ Спасибо! Ваша заявка принята. Наш оператор свяжется с вами в ближайшее время!", reply_markup=kb)
    await state.clear()

@dp.callback_query(F.data == "repeat_order")
async def repeat_order_handler(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    last_order = data.get("last_order")
    
    if not last_order:
        await callback.message.edit_text("У вас пока нет прошлых заказов для повтора.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🏠 В меню", callback_data="back")]]))
        return

    try:
        if str(callback.from_user.id) != str(ADMIN_ID):
            await bot.send_message(ADMIN_ID, f"🔄 ПОВТОР ЗАКАЗА\n{last_order}\nКлиент: @{callback.from_user.username}")
    except Exception as e:
        logging.error(f"Ошибка отправки: {e}")
        
    await callback.message.edit_text("✅ Повторили ваш прошлый заказ! Ожидайте звонка оператора.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🏠 В меню", callback_data="back")]]))
    await callback.answer()

@dp.callback_query(F.data == "share_bot")
async def share_bot_handler(callback: types.CallbackQuery):
    bot_username = (await bot.get_me()).username
    share_url = f"https://t.me/{bot_username}"
    text = f"Понравился сервис? Поделитесь ботом с друзьями!\n\nСсылка для пересылки: {share_url}"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤝 Поделиться", url=f"https://t.me/share/url?url={share_url}&text=Попробуй%20этот%20сервис!")],
        [InlineKeyboardButton(text="🏠 В меню", callback_data="back")]
    ])
    await callback.message.edit_text(text, reply_markup=kb)

@dp.callback_query(F.data == "rate")
async def rate_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Пожалуйста, оцените нашу работу от 1 до 5 (напишите цифру):")
    await state.set_state(OrderState.waiting_for_review)

@dp.message(OrderState.waiting_for_review)
async def process_review(message: types.Message, state: FSMContext):
    try:
        if str(message.from_user.id) != str(ADMIN_ID):
            await bot.send_message(ADMIN_ID, f"⭐ Новый отзыв: {message.text}")
    except Exception as e:
        logging.error(f"Ошибка: {e}")
    await message.answer("Спасибо за отзыв! Нам важно ваше мнение.")
    await state.clear()

@dp.callback_query(F.data == "complaint")
async def complaint_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Нам жаль, что что-то пошло не так. Опишите проблему и оставьте телефон для связи:")
    await state.set_state(OrderState.waiting_for_complaint)

@dp.message(OrderState.waiting_for_complaint)
async def process_complaint(message: types.Message, state: FSMContext):
    try:
        if str(message.from_user.id) != str(ADMIN_ID):
            await bot.send_message(ADMIN_ID, f"🚨 ЖАЛОБА:\n{message.text}")
    except Exception as e:
        logging.error(f"Ошибка: {e}")
    await message.answer("Спасибо, мы передали руководству. С вами свяжутся.")
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
