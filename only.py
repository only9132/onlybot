import asyncio
import random
import string
import aiohttp

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

BOT_TOKEN = "8758713959:AAEd2qOqSy3eyCyefPGEXt4Gox9THuNZpWA"
CRYPTO_TOKEN = "562858:AAlWuPvOsQpOHECm2u2JhSrD6WXy3GDXRNT"

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher()
CRYPTO_API = "https://pay.crypt.bot/api"

users = {}
orders_count = 260401

# ===================== ГЕНЕРАЦИЯ =====================
def gen_acc():
    return ''.join(random.choices(string.ascii_uppercase, k=10)) + ":" + \
           ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))

def gen_accounts(n):
    return "\n".join(gen_acc() for _ in range(n))

def gen_order():
    global orders_count
    orders_count += 1
    return f"ORD{orders_count}"

def gen_code():
    return str(random.randint(1000, 9999))

# ===================== CRYPTO =====================
async def create_invoice(amount, desc):
    async with aiohttp.ClientSession() as s:
        headers = {"Crypto-Pay-API-Token": CRYPTO_TOKEN}
        data = {"asset": "USDT", "amount": amount, "description": desc}
        async with s.post(f"{CRYPTO_API}/createInvoice", json=data, headers=headers) as r:
            return await r.json()

async def check_invoice(iid):
    async with aiohttp.ClientSession() as s:
        headers = {"Crypto-Pay-API-Token": CRYPTO_TOKEN}
        async with s.get(f"{CRYPTO_API}/getInvoices?invoice_ids={iid}", headers=headers) as r:
            return await r.json()

# ===================== UI =====================
def menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Каталог | Catalog", callback_data="catalog")],
        [
            InlineKeyboardButton(text="💼 Работай с нами", callback_data="work"),
            InlineKeyboardButton(text="👥 Пригласи друга", callback_data="ref")
        ],
        [InlineKeyboardButton(text="⭐ Отзывы | Reviews", callback_data="reviews")],
        [
            InlineKeyboardButton(text="📌 Информация | FAQ", callback_data="faq"),
            InlineKeyboardButton(text="⚙️ Поддержка | Support", callback_data="support")
        ]
    ])

def back():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back")]
    ])

async def edit(call, text, kb):
    try:
        await call.message.edit_text(text, reply_markup=kb)
    except:
        await call.message.answer(text, reply_markup=kb)

# ===================== START =====================
@dp.message(CommandStart())
async def start(message: Message):
    uid = message.from_user.id
    args = message.text.split()

    if uid not in users:
        users[uid] = {"bal": 0, "friends": 0, "ref": None}

        if len(args) > 1:
            ref = int(args[1])
            if ref != uid and ref in users:
                users[uid]["ref"] = ref
                users[ref]["friends"] += 1

    text = """<b><i>👋 Рад тебя видеть!</i></b>

💸 <b>Ищешь проверенные аккаунты Cash App с балансом?</b>  
Ты попал туда, куда нужно — здесь только <b>надёжные и рабочие аккаунты</b> ✅  

<b>🏆 Почему выбирают нас?</b>  
• 💎 Высокое качество аккаунтов  
• ⚡️ Мгновенная выдача после оплаты  
• 🔒 Полная безопасность сделок  
• 💬 Поддержка 24/7  

<b><i>💲Выгодная цена, 💎отличное качество, ⚡️быстрая выдача — мы делаем всё на уровне.</i></b>
"""
    await message.answer(text, reply_markup=menu())

# ===================== КАТАЛОГ =====================
products = {
    "mini": (1, 7.99),
    "start": (3, 24),
    "plus": (5, 40),
    "max": (10, 80),
    "ultra": (20, 160)
}

def catalog_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Mini | 8$", callback_data="buy_mini"),
            InlineKeyboardButton(text="Start | 24$", callback_data="buy_start")
        ],
        [
            InlineKeyboardButton(text="Plus | 40$", callback_data="buy_plus"),
            InlineKeyboardButton(text="Max | 80$", callback_data="buy_max")
        ],
        [InlineKeyboardButton(text="Ultra | 160$", callback_data="buy_ultra")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back")]
    ])

@dp.callback_query(F.data == "catalog")
async def catalog(call: CallbackQuery):
    text = """<b>🛒 Прайс-лист:</b>

<b>Mini Case</b> — 1 аккаунт  
<b>Start Case</b> — 3 аккаунта  
<b>Plus Case</b> — 5 аккаунтов  
<b>Max Case</b> — 10 аккаунтов  
<b>Ultra Case</b> — 20 аккаунтов  

💡 <i>Выбери подходящий вариант ниже</i>
"""
    await edit(call, text, catalog_kb())

# ===================== ТОВАР =====================
def product_kb(name):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Купить", callback_data=f"pay_{name}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="catalog")]
    ])

@dp.callback_query(F.data.startswith("buy_"))
async def product(call: CallbackQuery):
    name = call.data.split("_")[1]
    count, price = products[name]

    text = f"""<b>📦 Информация товара:</b>

<b>├ Сервис:</b> Cash App  
<b>├ Кол-во:</b> {count} шт  
<b>╰ Стоимость:</b> ${price}  

💡 <i>После оплаты выдача происходит автоматически</i>
"""
    await edit(call, text, product_kb(name))

# ===================== ОПЛАТА =====================
@dp.callback_query(F.data.startswith("pay_"))
async def pay(call: CallbackQuery):
    name = call.data.split("_")[1]
    count, price = products[name]

    invoice = await create_invoice(price, f"ONLY SHOP | {name.upper()} CASE")
    url = invoice["result"]["pay_url"]
    iid = invoice["result"]["invoice_id"]

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Оплатить", url=url)],
        [InlineKeyboardButton(text="✅ Проверить оплату", callback_data=f"check_{iid}_{name}")]
    ])

    text = """💳 <b>Оплата заказа</b>

1️⃣ Нажми кнопку <b>Оплатить</b>  
2️⃣ Заверши оплату  
3️⃣ Вернись и нажми <b>Проверить оплату</b>  

⚡️ После подтверждения ты сразу получишь аккаунты
"""
    await edit(call, text, kb)

# ===================== ПРОВЕРКА =====================
@dp.callback_query(F.data.startswith("check_"))
async def check(call: CallbackQuery):
    _, iid, name = call.data.split("_")
    count, _ = products[name]

    data = await check_invoice(iid)
    status = data["result"]["items"][0]["status"]

    if status == "paid":
        order = gen_order()
        accs = gen_accounts(count)

        text = f"""✅ <b>Ваш заказ #{order} завершен!</b>

📦 <b>Аккаунты:</b>
<code>{accs}</code>

🙏 Спасибо за покупку!
"""
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❤️ Спасибо!", callback_data="back")]
        ])

        await edit(call, text, kb)
    else:
        await call.answer("❌ Оплата не найдена", show_alert=True)

# ===================== РАБОТА =====================
@dp.callback_query(F.data == "work")
async def work(call: CallbackQuery):
    text = """💸 <b>Доход вместе с нами</b>

╰ <i>Мы открываем возможность зарабатывать через партнёрство</i>

❓ <b>Что нужно делать?</b>  
• Приводить пользователей  
• Получать бонусы  

💰 <b>Условия:</b>  
• 15% от покупок  
• Выплаты аккаунтами  
• Доступ от $50 покупок  

🎩 Менеджер: @only_blef
"""
    await edit(call, text, back())

# ===================== РЕФ =====================
@dp.callback_query(F.data == "ref")
async def ref(call: CallbackQuery):
    u = call.from_user
    data = users[u.id]

    username = f"@{u.username}" if u.username else u.first_name
    link = f"https://t.me/onl1sh0pbot?start={u.id}"

    text = f"""👥 <b>Реферальная система</b>

Приглашай друзей и получай <b>5%</b> от их покупок

💰 Баланс: {username} — <b>${data['bal']:.2f}</b>  
👥 Друзей: <b>{data['friends']}</b>  

🔗 Ссылка:
{link}
"""
    await edit(call, text, back())

# ===================== ОСТАЛЬНОЕ =====================
@dp.callback_query(F.data == "reviews")
async def reviews(call: CallbackQuery):
    await edit(call, "<b>Отзывы:</b>\nhttps://t.me/+pLjbWlLwTBE3ZTRi", back())

@dp.callback_query(F.data == "faq")
async def faq(call: CallbackQuery):
    text = """<b>Кто мы и чем занимаемся</b>

<b>Здравствуйте. Меня зовут Тимур, я старший менеджер проекта @onl1sh0pbot
Моя задача обеспечить бесперебойную работу сервиса и помочь клиентам в решении любых технических вопросов.</b>

<b>Если вы не нашли ответа на свой вопрос в данном разделе - свяжитесь со мной напрямую:</b> @synonym1010

<b>Мы специализируемся на продаже CashApp-аккаунтов и гарантируем высокий уровень обслуживания.</b>

📊 <b>На сегодняшний день:</b>
• объём реализованных аккаунтов за последние полгода превысил <b>100.000$</b>;
• ежемесячно мы обслуживаем до <b>1000 постоянных клиентов</b>;
• сервис работает стабильно и прозрачно, обеспечивая надёжность каждой сделки.

💎 <b>Мы ценим каждого клиента и гарантируем качество!</b>
"""
    await edit(call, text, back())

@dp.callback_query(F.data == "support")
async def support(call: CallbackQuery):
    code = gen_code()
    await edit(call, f"⚙️ Поддержка\n\nКод: <b>{code}</b>\nОтправь менеджеру @only_blef", back())

@dp.callback_query(F.data == "back")
async def back_handler(call: CallbackQuery):
    await edit(call, "<b>Главное меню</b>", menu())

# ===================== RUN =====================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())