from aiogram.types import KeyboardButton, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


def get_main_menu():
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="📋 Инструкция"), KeyboardButton(text="🔗 Ввести ссылку")
    )
    builder.row(
        KeyboardButton(text="💎 Купить подписку"),
        KeyboardButton(text="📊 Моя подписка"),
    )
    builder.row(KeyboardButton(text="📞 Поддержка"))
    return builder.as_markup(resize_keyboard=True)


from .models import TariffPlan


def get_subscription_plans(plans: list[TariffPlan]):
    builder = InlineKeyboardBuilder()
    for plan in plans:
        builder.add(
            InlineKeyboardButton(
                text=f"{plan.name} - {plan.price}", callback_data="sub_" + str(plan.id)
            ),
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
        InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_subs"),
    )
    builder.adjust(1)
    return builder.as_markup()
