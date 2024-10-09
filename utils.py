import os
from datetime import datetime

import pandas as pd
from aiogram.types import Message, FSInputFile
from aiogram.fsm.context import FSMContext


from config import CSV_FILE


def create_file_if_not_exists() -> None:
    """
    Create the CSV file with headers if it doesn't exist or is empty.
    """
    if not os.path.exists(CSV_FILE) or os.stat(CSV_FILE).st_size == 0:
        with open(CSV_FILE, 'w', encoding='utf-8') as f:
            f.write("ID, Timestamp, Username, User_ID, Ammount, Message\n")


async def download_file(message: Message) -> FSInputFile:
    """
    Download the CSV file and return the file path.
    """

    try:
        # Check if the CSV file exists and has data
        if os.path.exists(CSV_FILE) and os.stat(CSV_FILE).st_size > 0:
            # Use FSInputFile for sending files
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
        # Parse the input message
        amount, description = message.text.split(", ")
        amount = float(amount)  # Convert the amount to a number

        # Retrieve the transaction type from the state
        user_data = await state.get_data()
        transaction_type = user_data["transaction_type"]

        # Determine the values for the Income and Expense columns based on the transaction type
        income = amount if transaction_type == "Приход" else 0.0
        expense = amount if transaction_type == "Расход" else 0.0

        # Prepare data to write to CSV file
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Current time in specified format
        username = message.from_user.username or "Unknown"  # Get username or default to "Unknown"
        user_id = message.from_user.id

        # Read existing CSV to determine the next ID value
        try:
            existing_data = pd.read_csv(CSV_FILE)
            next_id = existing_data.shape[0] + 1  # Determine next ID based on row count
        except pd.errors.EmptyDataError:
            # Handle the case when the CSV is empty
            next_id = 1

        # Append new data to the CSV file with separate columns for Income, Expense, and Description
        with open(CSV_FILE, 'a', encoding='utf-8') as f:
            f.write(f"{next_id}, {timestamp}, {username}, {user_id}, {income}, {expense}, {description}\n")

        # Read the updated CSV and send as a table to the user
        updated_data = pd.read_csv(CSV_FILE)
        await message.answer(f"Запись добавлена.\n\nОбновленная таблица данных:\n\n{updated_data.to_string(index=False)}")

        # Reset the state and ask for new transaction type
        await state.clear()
        await message.answer("Выберите тип следующей операции: Приход или Расход.", reply_markup=transaction_type_keyboard)

    except ValueError:
        await message.answer("Ошибка ввода. Пожалуйста, введите данные в формате: Сумма, Назначение")
    except Exception as e:
        await message.answer(f"Произошла ошибка: {str(e)}")