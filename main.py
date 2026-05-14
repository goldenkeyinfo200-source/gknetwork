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

ADMIN_GMAIL = os.getenv("ADMIN_GMAIL", "goldenkeyinfo200@gmail.com")

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


def guest_menu():
    return ReplyKeyboardMarkup(
        [
            ["🏢 Компания очиш"],
            ["👤 Агент бўлиш"],
            ["🛠 Тех. ёрдам"]
        ],
        resize_keyboard=True
    )


def company_menu():
    return ReplyKeyboardMarkup(
        [
            ["🚀 Иловага кириш"],
            ["👥 Агентлар", "🏠 Объектлар"],
            ["📊 Статистика", "💳 Тариф"],
            ["🎁 Referral", "🛠 Тех. ёрдам"]
        ],
        resize_keyboard=True
    )


def offer_menu():
    return ReplyKeyboardMarkup(
        [
            ["✅ Розиман"],
            ["❌ Рози эмасман"]
        ],
        resize_keyboard=True
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    user_state.pop(int(user_id), None)

    try:
        ss = get_sheet()
        sheet = ss.worksheet("Companies")
        records = sheet.get_all_records()

        for row in records:
            if str(row.get("TelegramID", "")) == user_id:
                await update.message.reply_text(
                    f"✅ Хуш келибсиз, {row.get('CompanyName', '')}",
                    reply_markup=company_menu()
                )
                return

    except Exception as e:
        print("START ERROR:", e)

    await update.message.reply_text(
        "GK NETWORK\n\nКеракли бўлимни танланг:",
        reply_markup=guest_menu()
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.message.from_user.id

    if text == "🛠 Тех. ёрдам":
        await update.message.reply_text(
            "🛠 Техник ёрдам\n\n📞 +998917468500"
        )
        return

    if text == "🏢 Компания очиш":
        user_state[user_id] = {
            "mode": "company",
            "step": "company_name"
        }
        await update.message.reply_text("Компания номини киритинг:")
        return

    if text == "👤 Агент бўлиш":
        await update.message.reply_text(
            "Ҳозирча компания регистрацияси орқали ишга туширамиз."
        )
        return

    if text == "🚀 Иловага кириш":
        await update.message.reply_text(
            f"🚀 GK NETWORK иловаси:\n{APPSHEET_LINK}"
        )
        return

    state = user_state.get(user_id)

    if not state:
        await update.message.reply_text(
            "Керакли бўлимни танланг:",
            reply_markup=guest_menu()
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
        state["password"] = text
        state["step"] = "offer"

        await update.message.reply_text(
            "📄 ОФЕРТА ШАРТНОМА\n\n"
            "GK NETWORK платформасидан фойдаланиш шартлари:\n\n"
            "1. Платформадаги маълумотлар фақат иш мақсадида фойдаланилади.\n"
            "2. Бошқа агент ёки компания мижозининг телефон рақами ва тўлиқ манзили очиқ кўрсатилмайди.\n"
            "3. Алоқа фақат тизим ёки масъул агент орқали амалга оширилади.\n"
            "4. Мижоз ва объект маълумотларини учинчи шахсларга бериш тақиқланади.\n"
            "5. Сохта маълумот киритиш ёки қоидаларни бузиш аккаунт блокланишига сабаб бўлади.\n"
            "6. Давом этиш орқали сиз ушбу шартларга рози эканлигингизни тасдиқлайсиз.\n\n"
            "Давом этиш учун “✅ Розиман” тугмасини босинг.",
            reply_markup=offer_menu()
        )
        return

    if step == "offer":
        if text == "❌ Рози эмасман":
            user_state.pop(user_id, None)
            await update.message.reply_text(
                "❌ Рўйхатдан ўтиш бекор қилинди.",
                reply_markup=guest_menu()
            )
            return

        if text != "✅ Розиман":
            await update.message.reply_text(
                "Давом этиш учун “✅ Розиман” тугмасини босинг.",
                reply_markup=offer_menu()
            )
            return

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
                ADMIN_GMAIL,
                state["login"],
                state["password"],
                "Trial",
                now.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d"),
                "Active",
                "TRUE",
                now.strftime("%Y-%m-%d %H:%M:%S"),
                now.strftime("%Y-%m-%d %H:%M:%S")
            ])

            user_state.pop(user_id, None)

            await update.message.reply_text(
                f"✅ Компания очилди\n\n"
                f"ID: {company_id}\n"
                f"Компания: {state['company_name']}\n\n"
                f"30 кунлик Trial актив.\n\n"
                f"Логин: {state['login']}\n"
                f"Парол: {state['password']}\n\n"
                f"🚀 GK NETWORK иловаси:\n{APPSHEET_LINK}",
                reply_markup=company_menu()
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
