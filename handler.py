import json
from aiogram import Router, F
from aiogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton,
    FSInputFile, CallbackQuery
)
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from qwen_ai import ask_qwen  # твоя асинхронная функция для запроса к ИИ

router = Router()

class ChatAIState(StatesGroup):
    chatting = State()

def main_menu():
    buttons = [
        [InlineKeyboardButton(text="📚 FAQ", callback_data="faq")],
        [InlineKeyboardButton(text="🛠 Техподдержка", callback_data="support")],
        [InlineKeyboardButton(text="🤖 Чат с ИИ", callback_data="chat_ai")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def ai_chat_menu():
    buttons = [
        [InlineKeyboardButton(text="❌ Завершить чат с ИИ", callback_data="exit_ai")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@router.message(F.text == "/start")
async def start_handler(message: Message):
    try:
        with open("welcome.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        text = data.get("text", "Добро пожаловать!")
    except Exception:
        text = "Добро пожаловать!"
    photo = FSInputFile("logo.jpg")
    await message.answer_photo(photo=photo, caption=text, reply_markup=main_menu())

@router.callback_query(F.data == "faq")
async def faq_callback(callback: CallbackQuery):
    try:
        with open("faq.json", "r", encoding="utf-8") as f:
            faq = json.load(f)
        for q in faq.get("questions", []):
            question = q.get("question", "Вопрос отсутствует")
            answer = q.get("answer", "Ответ отсутствует")
            if callback.message:
                await callback.message.answer(f"❓ {question}\n💡 {answer}")
    except Exception as e:
        if callback.message:
            await callback.message.answer("⚠ Ошибка при загрузке FAQ.")
        print("Ошибка FAQ:", e)
    await callback.answer()

@router.callback_query(F.data == "chat_ai")
async def chat_ai_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ChatAIState.chatting)
    if callback.message:
        await callback.message.answer(
            "🤖 Режим общения с ИИ включён. Напишите свой вопрос:",
            reply_markup=ai_chat_menu()
        )
    await callback.answer()

@router.callback_query(F.data == "exit_ai")
async def exit_ai_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    if callback.message:
        await callback.message.answer("🚫 Общение с ИИ завершено. Вы можете выбрать другую функцию.", reply_markup=main_menu())
    await callback.answer()

@router.message(ChatAIState.chatting)
async def handle_user_question(message: Message, state: FSMContext):
    await message.answer("⌛ Думаю над ответом...")
    try:
        prompt = message.text or ""
        response = await ask_qwen(prompt)
        await message.answer(response)
    except Exception as e:
        await message.answer("❗ Произошла ошибка при обращении к ИИ.")
        print("Ошибка при обращении к ИИ:", e)
