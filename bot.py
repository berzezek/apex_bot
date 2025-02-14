import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message

from utils import (
    create_file_if_not_exists,
    download_file,
    waiting_for_amount_and_description,
    transaction_type_keyboard,
    TransactionState
)

from config import TOKEN

# All handlers should be attached to the Router (or Dispatcher)
dp = Dispatcher(storage=MemoryStorage())  # Initialize Dispatcher with FSM storage

# Create the CSV file if it doesn't exist
create_file_if_not_exists()


@dp.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext) -> None:
    """
    This handler receives messages with `/start` command.
    """
    await message.answer(
        f"Привет, {html.bold(message.from_user.full_name)}!\nВыберите тип операции: Приход или Расход.",
        reply_markup=transaction_type_keyboard,
    )
    await state.set_state(TransactionState.waiting_for_transaction_type)


@dp.message(Command(commands=["download"]))
async def command_download_handler(message: Message) -> None:
    """
    This handler allows downloading the CSV file with the command `/download`.
    """
    await download_file(message)


@dp.message(TransactionState.waiting_for_transaction_type)
async def transaction_type_chosen(message: Message, state: FSMContext) -> None:
    """
    Handle the user's choice of transaction type (Income or Expense).
    """
    if message.text not in ["Приход", "Расход", "Завершить"]:
        await message.answer("Пожалуйста, выберите 'Приход', 'Расход' или 'Завершить'.")
        return

    if message.text == "Завершить":
        await message.answer("Вы завершили ввод операций.")
        await state.clear()  # Очищаем состояние и выходим из процесса
        return

    # Сброс состояния, если пользователь заново выбирает тип транзакции
    await state.clear()
    await state.update_data(transaction_type=message.text)
    await message.answer(
        f"Вы выбрали {message.text}. Пожалуйста, введите сумму и назначение через запятую, например: 1000, Зарплата"
    )
    await state.set_state(TransactionState.waiting_for_amount_and_description)


@dp.message(TransactionState.waiting_for_amount_and_description)
async def amount_and_description_received(message: Message, state: FSMContext) -> None:
    """
    Handles the reception of amount and description from the user 
    in the TransactionState.waiting_for_amount_and_description state.
    """
    await waiting_for_amount_and_description(message, state)


async def main() -> None:
    """
    Main entry point for the bot.
    """
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
