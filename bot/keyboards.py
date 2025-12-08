from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

def get_main_menu():
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="📋 Инструкция"),
        KeyboardButton(text="🔗 Ввести ссылку")
    )
    builder.row(
        KeyboardButton(text="💎 Купить подписку"),
        KeyboardButton(text="📊 Моя подписка")
    )
    builder.row(KeyboardButton(text="📞 Поддержка"))
    return builder.as_markup(resize_keyboard=True)

def get_subscription_plans():
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="1 месяц - 500₽", callback_data="sub_1"),
        InlineKeyboardButton(text="3 месяца - 1200₽", callback_data="sub_3"),
        InlineKeyboardButton(text="6 месяцев - 2000₽", callback_data="sub_6"),
        InlineKeyboardButton(text="12 месяцев - 3500₽", callback_data="sub_12")
    )
    builder.adjust(1)
    return builder.as_markup()

def get_admin_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="👥 Пользователи"))
    builder.row(KeyboardButton(text="📊 Статистика"))
    builder.row(KeyboardButton(text="📝 Добавить инструкцию"))
    builder.row(KeyboardButton(text="🔙 Главное меню"))
    return builder.as_markup(resize_keyboard=True)

def get_back_to_menu():
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="🔙 Главное меню"))
    return builder.as_markup(resize_keyboard=True)

def get_payment_methods():
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="💳 Банковская карта", callback_data="pay_card"),
        InlineKeyboardButton(text="🟢 ЮMoney", callback_data="pay_yoomoney"),
        InlineKeyboardButton(text="🔵 СБП", callback_data="pay_sbp"),
        InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_subs")
    )
    builder.adjust(1)
    return builder.as_markup()