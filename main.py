import os
import json
from datetime import datetime, timedelta

import gspread
from google.oauth2.service_account import Credentials

from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
APPSHEET_LINK = os.getenv("APPSHEET_LINK")
GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON")

print("SPREADSHEET_ID =", SPREADSHEET_ID)

user_state = {}

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]


def get_sheet():
    creds_dict = json.loads(GOOGLE_CREDENTIALS_JSON)
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    client = gspread.authorize(creds)

    print("OPENING:", SPREADSHEET_ID)

    return client.open_by_key(SPREADSHEET_ID)


def main_menu():
    return ReplyKeyboardMarkup(
        [
            ["Компания очиш"],
            ["Агент бўлиш"],
            ["Appga кириш"],
            ["Алоқа"]
        ],
        resize_keyboard=True
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_state.pop(user_id, None)

    await update.message.reply_text(
        "GK NETWORK\n\nКеракли бўлимни танланг:",
        reply_markup=main_menu()
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.message.from_user.id

    if text == "Алоқа":
        await update.message.reply_text("Админ: +998911430202")
        return

    if text == "Компания очиш":
        user_state[user_id] = {
            "mode": "company",
            "step": "company_name"
        }
        await update.message.reply_text("Компания номини киритинг:")
        return

    if text == "Агент бўлиш":
        await update.message.reply_text("Ҳозирча аввал компания регистрациясини тўлиқ ишлатиб оламиз.")
        return

    if text == "Appga кириш":
        await update.message.reply_text(f"AppSheet:\n{APPSHEET_LINK}")
        return

    state = user_state.get(user_id)

    if not state:
        await update.message.reply_text(
            "Керакли бўлимни танланг:",
            reply_markup=main_menu()
        )
        return

    if state.get("mode") == "company":
        await handle_company(update, user_id, text, state)


async def handle_company(update: Update, user_id: int, text: str, state: dict):
    step = state["step"]

    if step == "company_name":
        state["company_name"] = text
        state["step"] = "owner_name"
        await update.message.reply_text("Раҳбар исмини киритинг:")
        return

    if step == "owner_name":
        state["owner_name"] = text
        state["step"] = "owner_phone"
        await update.message.reply_text("Телефон рақам киритинг:")
        return

    if step == "owner_phone":
        state["owner_phone"] = text
        state["step"] = "login"
        await update.message.reply_text("Логин киритинг:")
        return

    if step == "login":
        state["login"] = text
        state["step"] = "password"
        await update.message.reply_text("Парол киритинг:")
        return

    if step == "password":
        password = text

        try:
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

            await update.message.reply_text(
                f"✅ Компания очилди\n\n"
                f"ID: {company_id}\n"
                f"Компания: {state['company_name']}\n\n"
                f"30 кунлик Trial актив.\n\n"
                f"Логин: {state['login']}\n"
                f"Парол: {password}\n\n"
                f"AppSheet:\n{APPSHEET_LINK}",
                reply_markup=main_menu()
            )

        except Exception as e:
            await update.message.reply_text(
                f"❌ Google Sheets'га ёзишда хато:\n\n{e}"
            )


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
