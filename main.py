import qrcode
from io import BytesIO
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes, \
    ConversationHandler
from telegram.request import HTTPXRequest

# ТОКЕН БОТА - ВАШ ТОКЕН
BOT_TOKEN = ""

# Состояния для Wi-Fi ConversationHandler
WAITING_FOR_ENCRYPTION, WAITING_FOR_SSID, WAITING_FOR_PASSWORD = range(3)

# Настройки размеров QR-кода
QR_SETTINGS = {
    "small": {"box_size": 5, "border": 2},
    "medium": {"box_size": 10, "border": 4},
    "large": {"box_size": 15, "border": 6}
}


async def set_commands(application):
    """Устанавливает кнопки команд в интерфейсе Telegram"""
    commands = [
        BotCommand("start", "Запустить бота и показать главное меню"),
        BotCommand("wifi", "Создать QR-код для Wi-Fi"),
        BotCommand("settings", "Настроить размер QR-кода"),
        BotCommand("help", "Получить помощь"),
        BotCommand("about", "Информация о боте"),
        BotCommand("cancel", "Отменить текущую операцию"),
    ]
    await application.bot.set_my_commands(commands)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Приветствие"""
    context.user_data.clear()

    keyboard = [
        [InlineKeyboardButton("📝 Создать QR из текста", callback_data="text_mode")],
        [InlineKeyboardButton("📶 Сделать Wi-Fi QR код", callback_data="wifi_start")],
        [InlineKeyboardButton("🎨 Настроить размер", callback_data="settings"),
         InlineKeyboardButton("❓ Помощь", callback_data="help")],
        [InlineKeyboardButton("ℹ️ О боте", callback_data="about")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = """👋 Привет! Я бот для создания QR-кодов.

📝 Что я умею:
• Превращать любой текст в QR-код (просто отправь мне текст или нажми на кнопку)
• Создавать QR-коды для Wi-Fi (гости подключатся в один клик)
• Менять размер QR-кодов (маленький/средний/большой)

👇 Просто выбери действие, отправь любой текст или нажми на кнопку!"""

    if update.callback_query:
        await update.callback_query.message.reply_text(text, reply_markup=reply_markup)
        try:
            await update.callback_query.message.delete()
        except:
            pass
        await update.callback_query.answer()
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)


async def text_mode_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начинает режим создания QR из текста"""
    query = update.callback_query
    await query.answer()

    text = """📝 Режим создания QR-кода из текста

Просто отправь мне любой текст или ссылку, и я сделаю QR-код.

Максимальная длина: 1000 символов.

❌ Для отмены нажми /cancel"""

    await query.message.reply_text(text)
    try:
        await query.message.delete()
    except:
        pass

    context.user_data["text_mode"] = True


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Помощь"""
    keyboard = [
        [InlineKeyboardButton("◀️ В главное меню", callback_data="back_to_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = """🤔 Всё очень просто!

📝 Обычный QR-код:
• Просто отправь мне любой текст или ссылку
• Или нажми на кнопку "Создать QR из текста" в меню

📶 Wi-Fi QR-код:
Нажми на кнопку в меню или напиши /wifi

🎨 Размер QR-кода:
Выбери через /settings

⚡️ Команды:
/start - Главное меню
/wifi - Wi-Fi QR
/settings - Размер
/help - Справка
/about - О боте
/cancel - Отменить действие

😊 Просто выбери нужное действие!"""

    await update.message.reply_text(text, reply_markup=reply_markup)


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """О боте"""
    keyboard = [
        [InlineKeyboardButton("◀️ В главное меню", callback_data="back_to_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = """🤖 QR Code Bot

Версия: 3.0

✅ Бесплатный и быстрый
🔒 Без сохранения данных
📱 Поддерживает WPA/WPA2/WEP
📝 Поддерживает любые тексты

😊 Спасибо, что пользуешься!"""

    await update.message.reply_text(text, reply_markup=reply_markup)


async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Настройки размера"""
    current_size = context.user_data.get("qr_size", "medium")
    size_names = {"small": "маленький", "medium": "средний", "large": "большой"}

    keyboard = [
        [InlineKeyboardButton(f"{'✅ ' if current_size == 'small' else ''}📏 Маленький", callback_data="size_small")],
        [InlineKeyboardButton(f"{'✅ ' if current_size == 'medium' else ''}📐 Средний", callback_data="size_medium")],
        [InlineKeyboardButton(f"{'✅ ' if current_size == 'large' else ''}📏 Большой", callback_data="size_large")],
        [InlineKeyboardButton("◀️ Назад в меню", callback_data="back_to_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = f"🎨 Настройка размера\n\nСейчас у тебя выбран {size_names[current_size]} размер.\n\nКакой хочешь?"

    await update.message.reply_text(text, reply_markup=reply_markup)


async def generate_text_qr(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Генерирует QR-код из текста"""
    size = context.user_data.get("qr_size", "medium")
    user_settings = QR_SETTINGS[size]

    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=user_settings["box_size"],
            border=user_settings["border"],
        )

        qr.add_data(text)
        qr.make(fit=True)

        qr_image = qr.make_image(fill_color="black", back_color="white")

        bio = BytesIO()
        qr_image.save(bio, 'PNG')
        bio.seek(0)

        if len(text) > 100:
            preview = text[:100] + "..."
        else:
            preview = text

        keyboard = [
            [InlineKeyboardButton("➕ Ещё один QR", callback_data="new_qr"),
             InlineKeyboardButton("◀️ В меню", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_photo(
            photo=bio,
            caption=f"✅ Готово!\n\n📝 Вот QR-код для:\n{preview}\n\nЧто дальше?",
            reply_markup=reply_markup
        )

        context.user_data["text_mode"] = False

    except Exception as e:
        await update.message.reply_text(f"😅 Упс... Что-то пошло не так\n\nОшибка: {str(e)}")


# ============ Wi-Fi функции ============

async def wifi_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начинает процесс создания Wi-Fi QR-кода"""
    keyboard = [
        [InlineKeyboardButton("🔐 WPA/WPA2", callback_data="enc_WPA")],
        [InlineKeyboardButton("🔓 WEP", callback_data="enc_WEP")],
        [InlineKeyboardButton("🚫 Без пароля", callback_data="enc_nopass")],
        [InlineKeyboardButton("❌ Отмена", callback_data="cancel_wifi")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = """📶 Создание Wi-Fi QR-кода

Шаг 1 из 3: Выбери тип шифрования своей сети

Если не уверен - скорее всего WPA/WPA2, это сейчас везде стоит."""

    if update.callback_query:
        await update.callback_query.message.reply_text(text, reply_markup=reply_markup)
        try:
            await update.callback_query.message.delete()
        except:
            pass
        await update.callback_query.answer()
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)

    return WAITING_FOR_ENCRYPTION


async def encryption_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает выбор шифрования"""
    query = update.callback_query
    await query.answer()

    if query.data == "cancel_wifi":
        await query.message.reply_text("❌ Отменил. Если передумаешь - просто напиши /wifi 😊")
        try:
            await query.message.delete()
        except:
            pass
        return ConversationHandler.END

    encryption = query.data.split("_")[1]
    context.user_data["wifi_encryption"] = encryption

    encryption_names = {"WPA": "WPA/WPA2", "WEP": "WEP", "nopass": "без пароля"}

    text = f"""✅ Шаг 2 из 3: Выбрано шифрование - {encryption_names[encryption]}

📝 Теперь напиши название Wi-Fi сети (SSID)

❌ Отмена - напиши /cancel"""

    await query.message.reply_text(text)
    try:
        await query.message.delete()
    except:
        pass

    return WAITING_FOR_SSID


async def ssid_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохраняет SSID"""
    ssid = update.message.text
    context.user_data["wifi_ssid"] = ssid

    encryption = context.user_data.get("wifi_encryption")

    if encryption == "nopass":
        return await generate_wifi_qr(update, context)
    else:
        text = f"""✅ Шаг 3 из 3: Сеть называется {ssid}

🔑 Теперь введи пароль от этой сети

❌ Отмена - напиши /cancel"""

        await update.message.reply_text(text)
        return WAITING_FOR_PASSWORD


async def password_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохраняет пароль"""
    password = update.message.text
    context.user_data["wifi_password"] = password
    return await generate_wifi_qr(update, context)


async def generate_wifi_qr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Генерирует Wi-Fi QR-код"""
    ssid = context.user_data["wifi_ssid"]
    encryption = context.user_data.get("wifi_encryption")
    password = context.user_data.get("wifi_password", "")

    if encryption == "nopass":
        wifi_string = f"WIFI:T:nopass;S:{ssid};P:;H:false;"
    else:
        wifi_string = f"WIFI:T:{encryption};S:{ssid};P:{password};H:false;"

    processing_msg = await update.message.reply_text("🔄 Создаю QR-код...")

    try:
        size = context.user_data.get("qr_size", "medium")
        user_settings = QR_SETTINGS[size]

        qr = qrcode.QRCode(
            version=2,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=user_settings["box_size"],
            border=user_settings["border"],
        )

        qr.add_data(wifi_string)
        qr.make(fit=True)

        qr_image = qr.make_image(fill_color="black", back_color="white")

        bio = BytesIO()
        qr_image.save(bio, 'PNG')
        bio.seek(0)

        encryption_names = {"WPA": "WPA/WPA2", "WEP": "WEP", "nopass": "без пароля"}

        info = f"""✅ Wi-Fi QR-код готов!

📶 Сеть: {ssid}
🔒 Шифрование: {encryption_names[encryption]}"""

        if encryption != "nopass":
            info += f"\n🔑 Пароль: {password}"

        info += """

✨ Как использовать:
1. Открой камеру на телефоне
2. Наведи на QR-код
3. Нажми на всплывающее уведомление
4. Телефон сам подключится к Wi-Fi!

😊 Удобно же, правда?"""

        keyboard = [
            [InlineKeyboardButton("📶 Ещё один Wi-Fi QR", callback_data="wifi_start"),
             InlineKeyboardButton("📝 Создать QR из текста", callback_data="text_mode"),
             InlineKeyboardButton("◀️ В меню", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_photo(
            photo=bio,
            caption=info,
            reply_markup=reply_markup
        )

        await processing_msg.delete()

        context.user_data.pop("wifi_ssid", None)
        context.user_data.pop("wifi_encryption", None)
        context.user_data.pop("wifi_password", None)

    except Exception as e:
        await processing_msg.edit_text(f"😅 Ошибка: {str(e)}")

    return ConversationHandler.END


# ============ Основные обработчики ============

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена операции"""
    context.user_data.clear()
    await update.message.reply_text("❌ Отменил, как ты и просил. Если что - я тут 😊")
    return ConversationHandler.END


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текста для QR-кода"""
    text = update.message.text

    if text.startswith('/'):
        return

    if context.user_data.get("wifi_encryption") and context.user_data.get("wifi_ssid") is None:
        await ssid_input(update, context)
        return
    elif context.user_data.get("wifi_password") is None and context.user_data.get("wifi_ssid"):
        await password_input(update, context)
        return

    if len(text) > 1000:
        await update.message.reply_text("😅 Текст слишком длинный! Максимум 1000 символов.")
        return

    processing_msg = await update.message.reply_text("🔄 Создаю QR-код...")
    await generate_text_qr(update, context, text)
    await processing_msg.delete()


async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка кнопок главного меню"""
    query = update.callback_query
    await query.answer()

    if query.data == "text_mode":
        await text_mode_start(update, context)

    elif query.data == "help":
        keyboard = [[InlineKeyboardButton("◀️ В главное меню", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        text = """❓ Помощь:

📝 Обычный QR: 
   • Просто отправь текст
   • Или нажми "Создать QR из текста"

📶 Wi-Fi QR: нажми на кнопку или /wifi
🎨 Размер: /settings
⚡️ Команды: /start, /wifi, /settings, /help, /about, /cancel"""

        await query.message.reply_text(text, reply_markup=reply_markup)
        try:
            await query.message.delete()
        except:
            pass

    elif query.data == "about":
        keyboard = [[InlineKeyboardButton("◀️ В главное меню", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        text = "🤖 QR Code Bot v3.0\n\n✅ Бесплатно\n🔒 Без сохранения данных\n📝 Любой текст в QR\n📶 Wi-Fi в QR\n😊 Удачи!"

        await query.message.reply_text(text, reply_markup=reply_markup)
        try:
            await query.message.delete()
        except:
            pass

    elif query.data == "settings":
        current_size = context.user_data.get("qr_size", "medium")
        size_names = {"small": "маленький", "medium": "средний", "large": "большой"}

        keyboard = [
            [InlineKeyboardButton("📏 Маленький", callback_data="size_small")],
            [InlineKeyboardButton("📐 Средний", callback_data="size_medium")],
            [InlineKeyboardButton("📏 Большой", callback_data="size_large")],
            [InlineKeyboardButton("◀️ Назад", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        text = f"🎨 Сейчас размер: {size_names[current_size]}\n\nВыбери новый:"

        await query.message.reply_text(text, reply_markup=reply_markup)
        try:
            await query.message.delete()
        except:
            pass

    elif query.data == "new_qr":
        keyboard = [
            [InlineKeyboardButton("📝 Создать QR из текста", callback_data="text_mode"),
             InlineKeyboardButton("📶 Wi-Fi QR", callback_data="wifi_start")],
            [InlineKeyboardButton("◀️ В меню", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        text = "📝 Что хочешь создать?\n\n• Отправь текст напрямую\n• Или выбери тип QR-кода"

        await query.message.reply_text(text, reply_markup=reply_markup)
        try:
            await query.message.delete()
        except:
            pass

    elif query.data == "back_to_menu":
        context.user_data.clear()
        keyboard = [
            [InlineKeyboardButton("📝 Создать QR из текста", callback_data="text_mode")],
            [InlineKeyboardButton("📶 Wi-Fi QR код", callback_data="wifi_start")],
            [InlineKeyboardButton("🎨 Размер", callback_data="settings"),
             InlineKeyboardButton("❓ Помощь", callback_data="help")],
            [InlineKeyboardButton("ℹ️ О боте", callback_data="about")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        text = "👋 Главное меню\n\nЧто будем делать? 👇"

        await query.message.reply_text(text, reply_markup=reply_markup)
        try:
            await query.message.delete()
        except:
            pass

    elif query.data.startswith("size_"):
        size = query.data.split("_")[1]
        if size in ["small", "medium", "large"]:
            context.user_data["qr_size"] = size
            size_names = {"small": "маленький", "medium": "средний", "large": "большой"}
            keyboard = [[InlineKeyboardButton("◀️ В меню", callback_data="back_to_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            text = f"✅ Теперь QR-коды будут {size_names[size]} размера!"

            await query.message.reply_text(text, reply_markup=reply_markup)
            try:
                await query.message.delete()
            except:
                pass


def main():
    """Запуск бота"""

    # Настройка подключения
    request = HTTPXRequest(
        connect_timeout=30.0,
        read_timeout=30.0,
        write_timeout=30.0,
        pool_timeout=30.0,
        http_version="1.1"
    )

    # Создание приложения
    application = Application.builder().token(BOT_TOKEN).request(request).build()

    # Установка команд
    application.post_init = set_commands

    # Добавление обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about_command))
    application.add_handler(CommandHandler("settings", settings_command))
    application.add_handler(CommandHandler("cancel", cancel))

    # Wi-Fi обработчик
    wifi_handler = ConversationHandler(
        entry_points=[
            CommandHandler("wifi", wifi_start),
            CallbackQueryHandler(wifi_start, pattern="^wifi_start$")
        ],
        states={
            WAITING_FOR_ENCRYPTION: [CallbackQueryHandler(encryption_choice, pattern="^(enc_|cancel_wifi)")],
            WAITING_FOR_SSID: [MessageHandler(filters.TEXT & ~filters.COMMAND, ssid_input)],
            WAITING_FOR_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, password_input)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(wifi_handler)

    # Обработка текста
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))

    # Остальные кнопки
    application.add_handler(CallbackQueryHandler(main_menu_callback))

    # Запуск
    print("=" * 50)
    print("🚀 Бот успешно запущен!")
    print("=" * 50)
    print("✅ Бот готов к работе")
    print("📝 Отправь любой текст - получи QR-код!")
    print("📶 Или нажми на кнопку 'Сделать Wi-Fi QR код'")
    print("🛑 Для остановки нажми Ctrl+C")
    print("=" * 50)

    try:
        application.run_polling(
            allowed_updates=["message", "callback_query"],
            drop_pending_updates=True,
            bootstrap_retries=3
        )
    except Exception as e:
        print(f"Ошибка при запуске: {e}")


if __name__ == "__main__":
    main()
