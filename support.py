import os
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

router = Router()

# Переменная для хранения ID администратора (установи при запуске)
ADMIN_ID = None

def setup_support(admin_id: int):
    global ADMIN_ID
    ADMIN_ID = admin_id

# Состояния для чата поддержки
class SupportChat(StatesGroup):
    user_chatting = State()          # Пользователь пишет в поддержку
    admin_waiting_for_reply = State()  # Админ вводит ответ

# Активные чаты: ключ - user_id, значение - True/False (активен/завершен)
active_chats = {}

# Клавиатура для пользователя — кнопка "Завершить чат"
def end_chat_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Завершить чат", callback_data="end_chat")]
    ])

# Клавиатура для администратора — кнопки "Ответить" и "Завершить чат"
def reply_buttons(user_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✉ Ответить", callback_data=f"reply_to_{user_id}")],
        [InlineKeyboardButton(text="❌ Завершить чат", callback_data=f"end_chat_{user_id}")]
    ])

# Обработка нажатия кнопки "Техподдержка" (callback_data="support")
@router.callback_query(F.data == "support")
async def support_entry(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    active_chats[user_id] = True  # Чат открыт
    await callback.message.answer(
        "📩 Опишите вашу проблему. Администратор скоро ответит.",
        reply_markup=end_chat_keyboard()
    )
    await state.set_state(SupportChat.user_chatting)
    await callback.answer()

# Сообщение пользователя — отправляем администратору
@router.message(SupportChat.user_chatting)
async def user_message_to_admin(message: Message):
    user_id = message.from_user.id
    if not active_chats.get(user_id):
        await message.answer("❗ Ваш чат с поддержкой завершён. Нажмите кнопку 'Техподдержка', чтобы начать заново.")
        return

    text_for_admin = (
        f"📨 Сообщение от студента @{message.from_user.username or message.from_user.first_name} (ID: {user_id}):\n\n"
        f"{message.text}"
    )
    try:
        await message.bot.send_message(chat_id=ADMIN_ID, text=text_for_admin, reply_markup=reply_buttons(user_id))
        await message.answer("✅ Ваше сообщение отправлено в техподдержку.")
    except Exception as e:
        await message.answer("❗ Ошибка отправки сообщения администратору.")
        print(f"Ошибка отправки администратору: {e}")

# Админ нажал "Ответить" — переходим в состояние ожидания текста для ответа
@router.callback_query(F.data.startswith("reply_to_"))
async def admin_reply_start(callback: CallbackQuery, state: FSMContext):
    user_id_str = callback.data.removeprefix("reply_to_")
    try:
        user_id = int(user_id_str)
    except ValueError:
        await callback.answer("Ошибка: неверный ID пользователя", show_alert=True)
        return

    await state.update_data(target_user=user_id)
    await callback.message.answer("✏️ Введите сообщение для ответа студенту.")
    await state.set_state(SupportChat.admin_waiting_for_reply)
    await callback.answer()

# Админ вводит ответ — отправляем пользователю
@router.message(SupportChat.admin_waiting_for_reply)
async def admin_send_reply(message: Message, state: FSMContext):
    data = await state.get_data()
    target_user = data.get("target_user")

    if target_user is None:
        await message.answer("❗ Не удалось получить данные пользователя.")
        await state.clear()
        return

    if not active_chats.get(target_user):
        await message.answer("⚠ Пользователь завершил чат.")
        await state.clear()
        return

    try:
        await message.bot.send_message(
            chat_id=target_user,
            text=f"📬 Ответ от техподдержки:\n\n{message.text}",
            reply_markup=end_chat_keyboard()
        )
        await message.answer("✅ Ответ отправлен пользователю.")
    except Exception as e:
        await message.answer("❗ Ошибка при отправке сообщения пользователю.")
        print(f"Ошибка отправки пользователю: {e}")

    await state.clear()

# Пользователь завершил чат
@router.callback_query(F.data == "end_chat")
async def end_chat_user(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    active_chats.pop(user_id, None)
    await callback.message.answer("❎ Вы завершили чат с техподдержкой.")
    await state.clear()
    await callback.answer()
    if ADMIN_ID:
        try:
            await callback.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"⚠ Пользователь с ID {user_id} завершил чат."
            )
        except Exception as e:
            print(f"Ошибка при уведомлении администратора о завершении чата пользователем: {e}")
 
# Админ завершил чат для пользователя
@router.callback_query(F.data.startswith("end_chat_"))
async def end_chat_admin(callback: CallbackQuery, state: FSMContext):
    user_id_str = callback.data.removeprefix("end_chat_")
    try:
        user_id = int(user_id_str)
    except ValueError:
        await callback.answer("Ошибка: неверный ID пользователя", show_alert=True)
        return

    active_chats.pop(user_id, None)

    try:
        await callback.bot.send_message(chat_id=user_id, text="🔒 Чат с техподдержкой завершён администратором.")
    except Exception:
        pass

    await callback.message.answer("✅ Чат завершён.")
    await state.clear()
    await callback.answer()
