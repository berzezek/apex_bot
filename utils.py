import os
from datetime import datetime
import pandas as pd
from aiogram.types import Message, FSInputFile, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from config import CSV_FILE

# Кнопки для выбора типа транзакции с добавлением кнопки "Завершить"
transaction_type_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Приход"), KeyboardButton(text="Расход")],
        [KeyboardButton(text="Завершить")],  # Добавление кнопки "Завершить"
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

# Создание состояния для хранения текущего выбора пользователя
class TransactionState(StatesGroup):
    """
    TransactionState is a class that inherits from StatesGroup and represents the different states
    in a transaction process for a Telegram bot.
    """
    waiting_for_transaction_type = State()
    waiting_for_amount_and_description = State()


def create_file_if_not_exists() -> None:
    """
    Create the CSV file with headers if it doesn't exist or is empty.
    """
    if not os.path.exists(CSV_FILE) or os.stat(CSV_FILE).st_size == 0:
        with open(CSV_FILE, 'w', encoding='utf-8') as f:
            f.write("ID, Timestamp, Username, User_ID, Income, Expense, Description\n")


async def download_file(message: Message) -> FSInputFile:
    """
    Download the CSV file and return the file path.
    """
    try:
        if os.path.exists(CSV_FILE) and os.stat(CSV_FILE).st_size > 0:
            file = FSInputFile(CSV_FILE)
            await message.answer_document(document=file, caption="Вот ваш файл data.csv")
        else:
            await message.answer("Файл data.csv еще не содержит данных или не был создан.")
    except Exception as e:
        await message.answer(f"Ошибка при отправке файла: {str(e)}")


async def waiting_for_amount_and_description(message: Message, state: FSMContext) -> None:
    """
    Handle the amount and description provided by the user.
    """
    try:
        # Проверка, что сообщение содержит запятую и можно корректно распарсить
        if ', ' not in message.text:
            raise ValueError("Некорректный формат. Требуется запятая между суммой и назначением.")

        # Парсинг ввода
        parts = message.text.split(", ")
        if len(parts) != 2:
            raise ValueError("Некорректный формат. Ожидается только два значения: Сумма и Назначение.")

        # Проверка, что первое значение является числом
        try:
            amount = float(parts[0].strip())  # Преобразование строки в число и удаление лишних пробелов
        except ValueError:
            raise ValueError("Ошибка ввода. Первое значение должно быть числом (например, 100).")

        # Извлечение описания
        description = parts[1].strip()  # Удаление лишних пробелов из описания

        # Retrieve the transaction type from the state
        user_data = await state.get_data()
        transaction_type = user_data.get("transaction_type", "Неизвестно")

        # Determine the values for the Income and Expense columns based on the transaction type
        income = amount if transaction_type == "Приход" else 0.0
        expense = amount if transaction_type == "Расход" else 0.0

        # Prepare data to write to CSV file
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Current time in specified format
        username = message.from_user.username or "Unknown"  # Get username or default to "Unknown"
        user_id = message.from_user.id

        # Read existing CSV to determine the next ID value
        is_new_file = not os.path.exists(CSV_FILE) or os.stat(CSV_FILE).st_size == 0
        try:
            existing_data = pd.read_csv(CSV_FILE)
            next_id = existing_data.shape[0] + 1  # Determine next ID based on row count
        except pd.errors.EmptyDataError:
            next_id = 1

        # Если файл уже существует и не пуст, добавляем новую строку перед записью
        newline = "" if is_new_file else "\n"

        # Append new data to the CSV file with separate columns for Income, Expense, and Description
        with open(CSV_FILE, 'a', encoding='utf-8') as f:
            f.write(f"{newline}{next_id}, {timestamp}, {username}, {user_id}, {income}, {expense}, {description}\n")

        # Уведомить пользователя об успешной записи
        await message.answer(f"Запись добавлена:\nСумма: {amount}\nНазначение: {description}\nТип операции: {transaction_type}.")

        # Сброс состояния к начальному состоянию
        await state.set_state(TransactionState.waiting_for_transaction_type)

        # Снова предложить выбрать операцию или завершить
        await message.answer("Выберите тип следующей операции: Приход, Расход или Завершить.", reply_markup=transaction_type_keyboard)

    except ValueError as ve:
        await message.answer(f"Ошибка ввода: {ve}. Пожалуйста, введите данные в формате: Сумма, Назначение.")
    except Exception as e:
        await message.answer(f"Произошла ошибка: {str(e)}")