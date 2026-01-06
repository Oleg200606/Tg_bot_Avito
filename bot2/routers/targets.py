from aiogram import Router, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from aiogram.types import Message
from ..keyboards import ADD_TARGET_MESSAGE, get_main_menu, LIST_TARGETS_MESSAGE
from ..targets import get_targets, create_target, can_create_target

router = Router()


class AddTarget(StatesGroup):
    input_url = State()


CANCEL_BTN_TEXT = "Отмена"
CANCEL_MESSAGES = [CANCEL_BTN_TEXT, "отмена"]


def url_input_markup():
    markup = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=CANCEL_BTN_TEXT)]],
        input_field_placeholder="Ссылка на страницу на avito.ru",
        resize_keyboard=True,
    )
    return markup


@router.message(StateFilter(None), F.text == LIST_TARGETS_MESSAGE)
async def list_targets(message: Message):

    targets = get_targets(message.chat.id)
    answer = """<b>Ваши цели:</b> \n"""
    if len(targets) == 0:
        answer += "\nЗдесь пока ничего нет"
    else:
        for t in targets:
            answer += f"- <a href='{t.url}'>{t.title}</a> \n"
    await message.answer(answer, reply_markup=get_main_menu(message.chat.id))


@router.message(StateFilter(None), F.text == ADD_TARGET_MESSAGE)
async def add_target(message: Message, state: FSMContext):
    if not can_create_target(message.chat.id):
        await message.answer(
            text="❌ Вы не можете добавить новую цель.\n\nМожет пришло время повысить уровень подписки?",
            reply_markup=get_main_menu(message.chat.id),
        )
        return

    await message.answer(text="Введите ссылку:", reply_markup=url_input_markup())
    await state.set_state(AddTarget.input_url)


@router.message(AddTarget.input_url, F.text.in_(CANCEL_MESSAGES))
async def cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Действие отменено", reply_markup=get_main_menu(message.chat.id)
    )


def is_valid_url(url: str) -> bool:
    import validators

    if validators.url(url) is not True:
        return False

    if not "avito.ru" in url:
        return False

    return True


@router.message(AddTarget.input_url)
async def input_url(message: Message, state: FSMContext):
    if message.text is None:
        await message.answer(
            "Ввод некорректен, повторите", reply_markup=url_input_markup()
        )
        return

    if not is_valid_url(message.text):
        await message.answer(
            "Введена некорректная ссылка, повторите", reply_markup=url_input_markup()
        )
        return

    new_target = create_target(message.chat.id, message.text)
    if new_target is None:
        await state.clear()
        await message.answer(
            "😿 Что-то пошло не так", reply_markup=get_main_menu(message.chat.id)
        )
        return

    await message.answer(
        "😎 Новая цель добавлена", reply_markup=get_main_menu(message.chat.id)
    )
    await state.clear()
