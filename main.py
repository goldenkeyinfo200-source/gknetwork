import os
import json
from datetime import datetime, timedelta

import gspread
from google.oauth2.service_account import Credentials

from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
APPSHEET_LINK = os.getenv("APPSHEET_LINK")
GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

user_state = {}

def get_sheet():
    creds_dict = json.loads(GOOGLE_CREDENTIALS_JSON)

    creds = Credentials.from_service_account_info(
        creds_dict,
        scopes=SCOPES
    )

    client = gspread.authorize(creds)

    return client.open_by_key(SPREADSHEET_ID)

def main_menu():
    keyboard = [
        ["Компания очиш"],
        ["Агент бўлиш"],
        ["Appga кириш"],
        ["Алоқа"]
    ]

    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )

def start(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    if user_id in user_state:
        del user_state[user_id]

    update.message.reply_text(
        "GK NETWORK\n\nКеракли бўлимни танланг:",
        reply_markup=main_menu()
    )

def handle_message(update: Update, context: CallbackContext):
    text = update.message.text
    user_id = update.message.from_user.id

    if text == "Алоқа":
        update.message.reply_text(
            "Админ: +998911430202"
        )
        return

    if text == "Компания очиш":
        user_state[user_id] = {
            "step": "company_name"
        }

        update.message.reply_text(
            "Компания номини киритинг:"
        )
        return

    state = user_state.get(user_id)

    if not state:
        update.message.reply_text(
            "Керакли бўлимни танланг:",
            reply_markup=main_menu()
        )
        return

    step = state["step"]

    if step == "company_name":
        state["company_name"] = text
        state["step"] = "owner_name"

        update.message.reply_text(
            "Раҳбар исмини киритинг:"
        )
        return

    if step == "owner_name":
        state["owner_name"] = text
        state["step"] = "owner_phone"

        update.message.reply_text(
            "Телефон рақам киритинг:"
        )
        return

    if step == "owner_phone":
        state["owner_phone"] = text
        state["step"] = "login"

        update.message.reply_text(
            "Логин киритинг:"
        )
        return

    if step == "login":
        state["login"] = text
        state["step"] = "password"

        update.message.reply_text(
            "Парол киритинг:"
        )
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

        del user_state[user_id]

        update.message.reply_text(
            f"✅ Компания очилди\n\n"
            f"ID: {company_id}\n"
            f"Компания: {state['company_name']}\n\n"
            f"Логин: {state['login']}\n"
            f"Парол: {password}\n\n"
            f"{APPSHEET_LINK}",
            reply_markup=main_menu()
        )

def main():
    updater = Updater(BOT_TOKEN, use_context=True)

    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))

    dp.add_handler(
        MessageHandler(
            Filters.text & ~Filters.command,
            handle_message
        )
    )

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()