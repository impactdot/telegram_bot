import logging
import requests
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from aiogram.utils import executor
from datetime import datetime
from decouple import config
from aiogram.utils import executor
from aiogram.dispatcher.webhook import get_new_configured_app
from aiogram.types import Update
from aiogram import Upda


crypto_pairs = ["BTCUSDT", "ETHUSDT", "XRPUSDT", "LTCUSDT", "BNBUSDT", "ADAUSDT"]

# Create a reply keyboard
keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)

# Add cryptocurrency pairs in sets of three
rows = [crypto_pairs[i : i + 3] for i in range(0, len(crypto_pairs), 3)]
for row in rows:
    keyboard.row(*[KeyboardButton(pair) for pair in row])
keyboard.row(*[KeyboardButton("Confirm Selection"), KeyboardButton("/commands")])


TOKEN = config("TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)


WEBHOOK_HOST = "https://yourdomain.com"  # Your domain or IP address
WEBHOOK_PATH = f"/webhook/{TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

dp.middleware.setup(UpdateTypeMiddleware(allowed_updates=UpdateType.MESSAGE))


logging.basicConfig(level=logging.INFO)

active_tasks = {}
user_intervals = {}
user_selected_pairs = {}
start_prices = {}
user_percentages = {}


def fetch_volume(pairing):
    endpoint = "https://api.binance.com/api/v3/ticker/24hr"
    params = {"symbol": pairing}
    volume = requests.get(endpoint, params=params).json()["volume"]
    return float(volume)


def fetch_price(pairing):
    # Your code to fetch the price from Binance
    # ...
    endpoint = "https://api.binance.com/api/v3/avgPrice"

    params = {"symbol": pairing}
    price_now = requests.get(endpoint, params=params).json()["price"]

    return float(price_now)


def price_change_detection(price_1, price_2, percentage):
    return abs(price_1 - price_2) / price_1 >= percentage


def volume_change_detection(old_volume, new_volume, threshold=0.10):
    return (new_volume - old_volume) / old_volume >= threshold


async def background_task(chat_id):
    percentage = user_percentages.get(chat_id, 0.01)
    while chat_id in active_tasks:
        for pairing in user_selected_pairs.get(chat_id):
            # interval = user_intervals.get(chat_id, 5) * 60  # Convert minutes to seconds
            interval = user_intervals.get(chat_id, 5)  # Convert minutes to seconds
            start_price = start_prices.get((chat_id, pairing), fetch_price(pairing))
            print("start_price: ", start_price)
            # Fetch current price
            price_now = fetch_price(pairing)
            print("price_now: ", price_now)
            # Check if price change exceeds threshold
            if price_change_detection(start_price, price_now, percentage):
                await bot.send_message(
                    chat_id,
                    f"Price for {pairing} changed by more than {percentage*100}% in the last {interval/60} minutes! {start_price} -> {price_now}",
                )
            # else:
            #     await bot.send_message(
            #         chat_id,
            #         f"Price for {pairing} didn't change by {percentage*100}% in the last {interval/60} minutes. Current price: {price_now}",
            #     )
            start_prices[(chat_id, pairing)] = price_now
        await asyncio.sleep(interval)


async def volume_background_task(chat_id, threshold=0.10):
    previous_volumes = {}
    while chat_id in active_tasks:
        for pairing in user_selected_pairs.get(chat_id):
            old_volume = previous_volumes.get(pairing, fetch_volume(pairing))
            new_volume = fetch_volume(pairing)
            if volume_change_detection(old_volume, new_volume, threshold):
                await bot.send_message(
                    chat_id,
                    f"Trading volume for {pairing} increased by more than {threshold*100}% in the last 24 hours! Previous: {old_volume} -> Now: {new_volume}",
                )
            previous_volumes[pairing] = new_volume
        await asyncio.sleep(86400)  # Sleep for 24 hours


@dp.message_handler(lambda message: message.text in crypto_pairs)
async def select_pair(message: types.Message):
    chat_id = message.chat.id
    selected_pair = message.text
    if chat_id not in user_selected_pairs:
        user_selected_pairs[chat_id] = []
    if selected_pair in user_selected_pairs[chat_id]:
        user_selected_pairs[chat_id].remove(selected_pair)
        await message.answer(f"You've deselected {selected_pair}.")
    else:
        user_selected_pairs[chat_id].append(selected_pair)
        await message.answer(f"You've selected {selected_pair} for tracking!")


@dp.message_handler(lambda message: message.text == "Confirm Selection")
async def confirm_selection(message: types.Message):
    chat_id = message.chat.id
    if chat_id in user_selected_pairs and user_selected_pairs[chat_id]:
        pairs = ", ".join(user_selected_pairs[chat_id])
        await message.answer(f"You're now tracking: {pairs}")
        active_tasks[chat_id] = True
        asyncio.create_task(background_task(chat_id))
        asyncio.create_task(volume_background_task(chat_id))
    else:
        await message.answer("Please select at least one cryptocurrency pair to track.")


@dp.message_handler(commands=["startalert"])
async def start_checking_price(message: types.Message):
    chat_id = message.chat.id
    active_tasks[chat_id] = True
    asyncio.create_task(background_task(chat_id))
    asyncio.create_task(volume_background_task(chat_id))


@dp.message_handler(commands=["start"])
async def send_welcome(message: types.Message):
    welcome_text = (
        "Welcome to your Telegram Alert Bot! 🚀\n\n"
        "This bot will notify you about price changes based on your preferences. \n"
        "You can set the time interval for checking prices with the /setinterval command. \n"
        "You can set the percentage of change with the /setpercentage command. \n"
        "To start receiving alerts, use the /startalert command. \n"
        "To stop receiving alerts, use the /stopalert command.\n"
        "Enjoy and stay updated! 💹"
    )
    await message.answer(welcome_text, reply_markup=keyboard)


@dp.message_handler(commands=["commands"])
async def commands(message: types.Message):
    commands_text = (
        "🛠 Commands 🛠\n\n"
        "/start - Welcome message\n"
        "/setinterval - Set the time interval for checking prices\n"
        "/setpercentage - Set the percentage of change\n"
        "/startalert - Start receiving price alerts\n"
        "/stopalert - Stop receiving price alerts\n"
        "Click on cryptocurrency pairs to select/deselect them for tracking\n"
        "Click 'Confirm Selection' to start tracking selected pairs\n"
    )
    await message.answer(commands_text, reply_markup=keyboard)


@dp.message_handler(commands=["stopalert"])
async def stop_checking_price(message: types.Message):
    chat_id = message.chat.id
    if chat_id in active_tasks:
        del active_tasks[chat_id]
        await message.answer("Stopped checking price.")
    else:
        await message.answer("You have no active price checking task.")


@dp.message_handler(commands=["setinterval"])
async def set_time_interval(message: types.Message):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("5 minutes", callback_data="5"))
    markup.add(InlineKeyboardButton("10 minutes", callback_data="10"))
    markup.add(InlineKeyboardButton("30 minutes", callback_data="30"))
    markup.add(InlineKeyboardButton("1 hour", callback_data="60"))
    await message.answer("Choose the time interval:", reply_markup=markup)


@dp.message_handler(commands=["setpercentage"])
async def set_percentage(message: types.Message):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("0.5%", callback_data="0.005"))
    markup.add(InlineKeyboardButton("1%", callback_data="0.01"))
    markup.add(InlineKeyboardButton("2%", callback_data="0.02"))
    markup.add(InlineKeyboardButton("5%", callback_data="0.05"))
    markup.add(InlineKeyboardButton("Custom", callback_data="custom_percentage"))
    await message.answer("Choose the percentage of change:", reply_markup=markup)


@dp.callback_query_handler(lambda c: c.data in ["5", "10", "30", "60"])
async def process_callback(callback_query: types.CallbackQuery):
    chat_id = callback_query.message.chat.id
    user_intervals[chat_id] = int(callback_query.data)
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(
        chat_id, f"Time interval set to {callback_query.data} minutes."
    )


@dp.callback_query_handler(
    lambda c: c.data in ["0.005", "0.01", "0.02", "0.05", "custom_percentage"]
)
async def process_percentage_callback(callback_query: types.CallbackQuery):
    chat_id = callback_query.message.chat.id
    if callback_query.data == "custom_percentage":
        await bot.send_message(
            chat_id, "Please enter the desired percentage (e.g., 3 for 3%)."
        )
    else:
        user_percentages[chat_id] = float(callback_query.data)
        await bot.answer_callback_query(callback_query.id)
        await bot.send_message(
            chat_id, f"Percentage set to {float(callback_query.data)*100}%."
        )


@dp.message_handler(lambda message: message.text.replace(".", "", 1).isdigit())
async def custom_percentage_input(message: types.Message):
    chat_id = message.chat.id
    try:
        percentage = float(message.text) / 100
        user_percentages[chat_id] = percentage
        await message.answer(f"Percentage set to {percentage*100}%.")
    except ValueError:
        await message.answer(
            "Invalid input. Please enter a valid percentage (e.g., 3 for 3%)."
        )


if __name__ == "__main__":
    from aiogram import executor

    executor.start_polling(dp, skip_updates=True)
