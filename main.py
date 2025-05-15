import asyncio
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

# Insert your bot token and Infura URL here
BOT_TOKEN = os.getenv("BOT_TOKEN", "7624939968:AAHdxmFyP04ZXYSDfyZFI2284FRst-erj3I")
INFURA_URL = os.getenv("INFURA_URL", "https://eth-mainnet.g.alchemy.com/v2/HZOmTXoCl7ZG7tgzp3D8DrmvJn0NlNrK")

web3 = Web3(Web3.HTTPProvider(INFURA_URL))

# USDT and USDC contract addresses (Ethereum mainnet)
USDT_CONTRACT = web3.to_checksum_address("0xdAC17F958D2ee523a2206206994597C13D831ec7")
USDC_CONTRACT = web3.to_checksum_address("0xA0b86991C6218b36c1d19D4a2e9Eb0cE3606eB48")

# ERC20 ABI snippet to read balanceOf
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function",
    }
]

usdt = web3.eth.contract(address=USDT_CONTRACT, abi=ERC20_ABI)
usdc = web3.eth.contract(address=USDC_CONTRACT, abi=ERC20_ABI)

def is_valid_eth_address(addr: str) -> bool:
    try:
        return web3.is_address(addr) and web3.is_checksum_address(web3.to_checksum_address(addr))
    except:
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send up to 10 Ethereum addresses (one per line or comma-separated) to check balances.")

async def check_balances(update: Update, context: ContextTypes.DEFAULT_TYPE):
    input_text = update.message.text
    raw_addresses = [addr.strip() for addr in input_text.replace(",", "\n").splitlines()]
    addresses = [addr for addr in raw_addresses if is_valid_eth_address(addr)]

    if not addresses:
        await update.message.reply_text("No valid Ethereum addresses found.")
        return

    if len(addresses) > 10:
        await update.message.reply_text("Please send no more than 10 addresses at a time.")
        return

    responses = []
    for addr in addresses:
        checksummed = web3.to_checksum_address(addr)
        eth_balance = web3.eth.get_balance(checksummed) / 1e18
        usdt_balance = usdt.functions.balanceOf(checksummed).call() / 1e6
        usdc_balance = usdc.functions.balanceOf(checksummed).call() / 1e6

        responses.append(
            f"📍 *{checksummed}*\n"
            f"  Ξ ETH: `{eth_balance:.5f}`\n"
            f"  💵 USDT: `{usdt_balance:.2f}`\n"
            f"  💵 USDC: `{usdc_balance:.2f}`\n"
        )

    await update.message.reply_text("\n\n".join(responses), parse_mode="Markdown")

async def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_balances))
    print("🤖 Bot is polling...")
    await app.run_polling()

if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    loop.run_forever()
