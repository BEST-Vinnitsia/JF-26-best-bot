from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import CommandStart
from datetime import datetime
from src.core.database import db
from src.core.config import settings
import re

router = Router()

# --- СТАНИ РЕЄСТРАЦІЇ ---
class RegState(StatesGroup):
    name = State()
    age = State()
    phone = State()
    email = State()
    university = State()
    custom_uni = State() # Для вводу "Іншого" або "Коледжу"
    experience = State()
    additional_info = State()
    days = State()
    consent = State()
    source = State()

# ==========================================
# ГОЛОВНЕ МЕНЮ (/start)
# ==========================================
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear() # Очищаємо стан на випадок, якщо юзер перезапустив бота
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="ℹ️ Загальна інформація", callback_data="menu_info")],
        [InlineKeyboardButton(text="📋 Реєстрація", callback_data="menu_reg")],
        [InlineKeyboardButton(text="👨‍💻 Організатори", callback_data="menu_org")]
    ])
    
    text = (
        "Привіт, майбутній учаснику! 👋\n\n"
        "Ласкаво просимо до офіційного бота Ярмарку Кар’єри від BEST Vinnytsia.\n"
        "Цей бот може:\n"
        "ℹ️ Розповісти все необхідне про Ярмарок Кар’єри;\n"
        "📋 Допомогти зареєструватись на подію;\n"
        "👨‍💻 Дізнатись більше про організаторів;\n"
        "⏳ Нагадати про проведення події.\n\n"
        "Реєструйся та не упусти можливість знайти роботу своєї мрії!"
    )
    await message.answer(text, reply_markup=kb)

# --- КНОПКИ ГОЛОВНОГО МЕНЮ ---
@router.callback_query(F.data == "menu_info")
async def show_info(callback: CallbackQuery):
    await callback.message.answer("Коротко про Ярмарок Кар'єри від PR. Більш детальна інформація про Ярмарок Кар'єри розміщена на сайті: ")
    await callback.answer()

@router.callback_query(F.data == "menu_org")
async def show_org(callback: CallbackQuery):
    await callback.message.answer("Інформація про Core Team i BEST.\nПосилання на сайт: ")
    await callback.answer()


# ==========================================
# ПОЧАТОК РЕЄСТРАЦІЇ
# ==========================================
@router.callback_query(F.data == "menu_reg")
async def start_registration(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Як компанії будуть до тебе звертатись?\nНапиши своє повне ПІБ👇:")
    await state.set_state(RegState.name)
    await callback.answer()

# 1. ПІБ -> Вік
@router.message(RegState.name, F.text)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Скільки тобі років?:")
    await state.set_state(RegState.age)

# 2. Вік -> Телефон
@router.message(RegState.age, F.text)
async def process_age(message: Message, state: FSMContext):
    # Перевіряємо, чи ввели саме цифри і чи вік адекватний (від 14 до 99 років)
    if not message.text.isdigit() or not (14 <= int(message.text) <= 99):
        return await message.answer("❌ Будь ласка, введи реальний вік цифрами (наприклад, 18):")
    
    await state.update_data(age=int(message.text)) # Зберігаємо в БД як число!
    
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Поділитися контактом", request_contact=True)]],
        resize_keyboard=True, one_time_keyboard=True
    )
    await message.answer("Як компанії з тобою будуть контактувати?\nНомер телефону:", reply_markup=kb)
    await state.set_state(RegState.phone)

# 3. Телефон -> Пошта
@router.message(RegState.phone, F.contact | F.text)
async def process_phone(message: Message, state: FSMContext):
    if message.contact:
        phone = message.contact.phone_number
    else:
        phone = message.text
        # Перевірка: чи схоже це на телефон (плюс, цифри, довжина 10-15 символів)
        phone_pattern = re.compile(r"^\+?[0-9\s\-\(\)]{10,15}$")
        if not phone_pattern.match(phone):
            return await message.answer("❌ Невірний формат телефону. Напиши номер цифрами (наприклад, +380987654321) або натисни кнопку нижче:")

    await state.update_data(phone=str(phone))
    
    remove_msg = await message.answer("...", reply_markup=ReplyKeyboardRemove())
    await remove_msg.delete()
    
    await message.answer("Електронна пошта:")
    await state.set_state(RegState.email)

# 4. Пошта -> Університет
@router.message(RegState.email, F.text)
async def process_email(message: Message, state: FSMContext):
    email = message.text
    # Перевірка: чи є текст до @, сама @, текст після, крапка і домен
    email_pattern = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")
    if not email_pattern.match(email):
        return await message.answer("❌ Невірний формат. Будь ласка, введи коректну електронну пошту (наприклад, name@gmail.com):")

    await state.update_data(email=email)
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="ВНТУ", callback_data="uni_ВНТУ"), InlineKeyboardButton(text="ДонНУ", callback_data="uni_ДонНУ")],
        [InlineKeyboardButton(text="ВНМУ", callback_data="uni_ВНМУ"), InlineKeyboardButton(text="ВДПУ", callback_data="uni_ВДПУ")],
        [InlineKeyboardButton(text="ВНАУ", callback_data="uni_ВНАУ"), InlineKeyboardButton(text="ВФЕУ", callback_data="uni_ВФЕУ")],
        [InlineKeyboardButton(text="ВТЕІ ДТЕУ", callback_data="uni_ВТЕІ ДТЕУ")],
        [InlineKeyboardButton(text="🎒 Ще в коледжі", callback_data="uni_college")],
        [InlineKeyboardButton(text="✍️ Інше", callback_data="uni_other")]
    ])
    await message.answer("Де ти навчаєшся?\nОбери свій університет:", reply_markup=kb)
    await state.set_state(RegState.university)

# 5. Університет (Обробка кнопок)
@router.callback_query(RegState.university, F.data.startswith("uni_"))
async def process_university(callback: CallbackQuery, state: FSMContext):
    uni_choice = callback.data.split("_")[1]
    
    # Якщо вибрали Інше або Коледж - просимо написати
    if uni_choice == "other":
        await callback.message.edit_text("Введи назву свого університету:")
        await state.set_state(RegState.custom_uni)
    elif uni_choice == "college":
        await callback.message.edit_text("Введи назву свого коледжа:")
        await state.set_state(RegState.custom_uni)
    else:
        # Якщо стандартний - зберігаємо і йдемо далі
        await state.update_data(university=uni_choice)
        await ask_experience(callback.message, state)
        
    await callback.answer()

# 5.1 Ручний ввід Університету/Коледжу
@router.message(RegState.custom_uni, F.text)
async def process_custom_uni(message: Message, state: FSMContext):
    await state.update_data(university=message.text)
    await ask_experience(message, state)

# Допоміжна функція для кроку з досвідом (щоб не дублювати код)
async def ask_experience(message: Message, state: FSMContext):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭ Досвіду роботи немає", callback_data="exp_skip")]
    ])
    await message.answer(
        "Чи був у тебе досвід роботи?\n"
        "Надішли резюме у форматі .pdf чи посилання на Github, LinkedIn, персональний сайт. "
        "Або опиши: сфера роботи, посада, період роботи",
        reply_markup=kb
    )
    await state.set_state(RegState.experience)

# 6. Досвід (текст, файл або пропуск) -> Дод. інфа
@router.message(RegState.experience, F.text | F.document)
async def process_exp_msg(message: Message, state: FSMContext):
    # Зберігаємо текст або ID файлу, якщо кинули PDF
    exp_data = message.document.file_id if message.document else message.text
    await state.update_data(experience=exp_data)
    await message.answer("Додаткова інформація, яку розповів б компаніям:")
    await state.set_state(RegState.additional_info)

@router.callback_query(RegState.experience, F.data == "exp_skip")
async def process_exp_skip(callback: CallbackQuery, state: FSMContext):
    await state.update_data(experience="Немає")
    await callback.message.edit_text("Додаткова інформація, яку розповів б компаніям:")
    await state.set_state(RegState.additional_info)

# 7. Дод. інфа -> Дні
@router.message(RegState.additional_info, F.text)
async def process_additional(message: Message, state: FSMContext):
    await state.update_data(additional_info=message.text)
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="День 1", callback_data="days_1"), InlineKeyboardButton(text="День 2", callback_data="days_2")],
        [InlineKeyboardButton(text="Всі 🔥", callback_data="days_all")]
    ])
    await message.answer("Дні події на які прийдеш:", reply_markup=kb)
    await state.set_state(RegState.days)

# 8. Дні -> Звідки дізналися
@router.callback_query(RegState.days, F.data.startswith("days_"))
async def process_days(callback: CallbackQuery, state: FSMContext):
    days = callback.data.split("_")[1]
    
    # Виправляємо збереження днів у базу
    if days == "1":
        days_db = "День 1"
    elif days == "2":
        days_db = "День 2"
    else:
        days_db = "Обидва"
        
    await state.update_data(days=days_db)
    # Перед фінальним кроком питаємо згоду на передачу даних компаніям
    consent_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="погоджуюсь", callback_data="consent_accept")]
    ])
    await callback.message.edit_text(
        "Чи ви погоджуєтесь що ваші данні будуть передані компаніям які беруть участь в Ярмарку Кар'єри",
        reply_markup=consent_kb
    )
    await state.set_state(RegState.consent)


# Обробник підтвердження згоди -> показати варіанти, звідки дізналися (source)
@router.callback_query(RegState.consent, F.data == "consent_accept")
async def process_consent(callback: CallbackQuery, state: FSMContext):
    # Показуємо ті самі опції, що й раніше для source
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📸 Інстаграм", callback_data="src_Instagram"), InlineKeyboardButton(text="✈️ Телеграм", callback_data="src_Telegram")],
        [InlineKeyboardButton(text="🗣 Друзі", callback_data="src_Friends"), InlineKeyboardButton(text="📄 Оголошення", callback_data="src_Ads")],
        [InlineKeyboardButton(text="👨‍🏫 Викладачі", callback_data="src_Teachers")]
    ])

    await callback.message.edit_text("Звідки дізналися:", reply_markup=kb)
    await state.set_state(RegState.source)
    await callback.answer()

# 9. Фініш та збереження в БД
@router.callback_query(RegState.source, F.data.startswith("src_"))
async def process_source(callback: CallbackQuery, state: FSMContext):
    source = callback.data.split("_")[1]
    data = await state.get_data()
    
    # Формуємо документ для бази
    user_doc = {
        "user_id": callback.from_user.id,
        "username": callback.from_user.username,
        "full_name": data.get("name"),
        "age": data.get("age"),
        "phone": data.get("phone"),
        "email": data.get("email"),
        "university": data.get("university"),
        "experience": data.get("experience"),
        "additional_info": data.get("additional_info"),
        "days": data.get("days"),
        "source": source,
        "registered_at": datetime.utcnow()
    }
    
    try:
        collection = db.client[settings.DB_NAME]["users"]
        # Зберігаємо або оновлюємо, щоб не було помилок дублікатів
        await collection.update_one(
            {"user_id": callback.from_user.id},
            {"$set": user_doc},
            upsert=True
        )
        
        await callback.message.edit_text(
            "✅ **Реєстрація успішна!**\n\n"
            "Чекаємо на тебе на івенті! Деталі надішлемо згодом.",
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"Помилка БД: {e}")
        await callback.message.edit_text("❌ Виникла помилка при збереженні. Спробуй пізніше.")
    
    await state.clear()