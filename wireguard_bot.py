import asyncio
import dotenv
import os
import subprocess

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.types import Message
from aiogram.filters import Command, CommandStart
from aiogram.enums import ParseMode

dotenv.load_dotenv()
TOKEN = os.getenv("TOKEN")

bot = Bot(TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

async def run_command(command, inputs=None):
    proc = await asyncio.create_subprocess_shell(command,
                                                 stdin=asyncio.subprocess.PIPE,
                                                 stdout=asyncio.subprocess.PIPE,
                                                 stderr=asyncio.subprocess.PIPE)
    if inputs:
        for inp in inputs:
            proc.stdin.write(f"{inp}\n".encode())
            await proc.stdin.drain()

    stdout, stderr = await proc.communicate()
    return stdout.decode().strip(), stderr.decode().strip()

async def add_wireguard_user(username):
    command = "./wireguard-install.sh"
    inputs = ["1", username, ""]
    stdout, stderr = await run_command(command, inputs)
    return stdout or stderr

async def remove_wireguard_user(username):
    command = "./wireguard-install.sh"
    list_users_command = "echo '2\n' | ./wireguard-install.sh"
    stdout, _ = await run_command(list_users_command)
    
    user_line = next((line for line in stdout.splitlines() if username in line), None)
    if not user_line:
        return f"User {username} not found."
    
    user_number = user_line.split(")")[0].strip()
    inputs = ["2", user_number, "y"]
    stdout, stderr = await run_command(command, inputs)
    return stdout or stderr

async def list_wireguard_users():
    command = "echo '2\n' | ./wireguard-install.sh"
    stdout, stderr = await run_command(command)
    return stdout or stderr

@dp.startup()
async def on_startup() -> None:
    await bot.delete_webhook(True)

@dp.message(CommandStart())
async def start(message: Message) -> None:
    await message.answer(f"Hello, <b>{message.from_user.first_name}</b>! Use /help to see available commands.")

@dp.message(Command("help"))
async def help_command(message: Message) -> None:
    help_text = (
        "Available commands:\n"
        "/add_user <username> - Add a new WireGuard user\n"
        "/remove_user <username> - Remove an existing WireGuard user\n"
        "/list_users - List all WireGuard users"
    )
    await message.answer(help_text)

@dp.message(Command("add_user"))
async def add_user(message: Message) -> None:
    args = message.get_args().split()
    if len(args) != 1:
        await message.answer("Usage: /add_user <username>")
        return
    
    username = args[0]
    result = await add_wireguard_user(username)
    await message.answer(result)

@dp.message(Command("remove_user"))
async def remove_user(message: Message) -> None:
    args = message.get_args().split()
    if len(args) != 1:
        await message.answer("Usage: /remove_user <username>")
        return
    
    username = args[0]
    result = await remove_wireguard_user(username)
    await message.answer(result)

@dp.message(Command("list_users"))
async def list_users(message: Message) -> None:
    result = await list_wireguard_users()
    await message.answer(result)

@dp.message(F.text)
async def echo(message: Message) -> None:
    await message.send_copy(message.chat.id)

if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))
