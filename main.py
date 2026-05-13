import os
import json
import asyncio
from datetime import datetime, timedelta

import gspread
from google.oauth2.service_account import Credentials

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart

BOT_TOKEN = os.getenv("BOT_TOKEN")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
APPSHEET_LINK = os.getenv("APPSHEET_LINK")
GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

user_state = {}

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def get_sheet():
    creds_dict = json.loads(GOOGLE_CREDENTIALS_JSON)
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    client = gspread.authorize(creds)
    return client.open_by_key(SPREADSHEET_ID)

def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Компания очиш")],
            [KeyboardButton(text="Агент бўлиш")],
            [KeyboardButton(text="Appga кириш")],
            [KeyboardButton(text="Алоқа")]
        ],
        resize_keyboard=True
    )

@dp.message(CommandStart())
async def start(message: Message):
    user_state.pop(message.from_user.id, None)
    await message.answer(
        "GK NETWORK\n\nКеракли бўлимни танланг:",
        reply_markup=main_menu()
    )

@dp.message(F.text == "Компания очиш")
async def company_start(message: Message):
    user_state[message.from_user.id] = {
        "mode": "company",
        "step": "company_name"
    }
    await message.answer("Компания номини киритинг:")

@dp.message(F.text == "Алоқа")
async def contact(message: Message):
    await message.answer("Админ: +998911430202")

@dp.message()
async def handle_steps(message: Message):
    user_id = message.from_user.id
    text = message.text

    state = user_state.get(user_id)

    if not state:
        await message.answer("Керакли бўлимни танланг:", reply_markup=main_menu())
        return

    if state["mode"] == "company":
        step = state["step"]

        if step == "company_name":
            state["company_name"] = text
            state["step"] = "owner_name"
            await message.answer("Раҳбар исмини киритинг:")
            return

        if step == "owner_name":
            state["owner_name"] = text
            state["step"] = "owner_phone"
            await message.answer("Телефон рақам киритинг:")
            return

        if step == "owner_phone":
            state["owner_phone"] = text
            state["step"] = "login"
            await message.answer("Логин киритинг:")
            return

        if step == "login":
            state["login"] = text
            state["step"] = "password"
            await message.answer("Парол киритинг:")
            return

        if step == "password":
            password = text

            ss = get_sheet()
            sheet = ss.worksheet("Companies")

            now = datetime.now()
            end_date = now + timedelta(days=30)
            company_id = "C-" + str(int(now.timestamp()))

            sheet.append_row([
                company_id,
                state["company_name"],
                state["owner_name"],
                state["owner_phone"],
                str(user_id),
                state["login"],
                password,
                "Trial",
                now.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d"),
                "Active",
                now.strftime("%Y-%m-%d %H:%M:%S")
            ])

            user_state.pop(user_id, None)

            await message.answer(
                f"✅ Компания рўйхатдан ўтди\n\n"
                f"CompanyID: {company_id}\n"
                f"Компания: {state['company_name']}\n\n"
                f"30 кунлик бепул фойдаланиш актив.\n\n"
                f"Логин: {state['login']}\n"
                f"Парол: {password}\n\n"
                f"AppSheet:\n{APPSHEET_LINK}",
                reply_markup=main_menu()
            )
            return

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())