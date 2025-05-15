import os
import logging
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from web3 import Web3
from decimal import Decimal

# Load API tokens from environment
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ETHERSCAN_API_KEY = os.environ.get("ETHERSCAN_API_KEY")
INFURA_URL = os.environ.get("INFURA_URL", "https://mainnet.infura.io/v3/YOUR_INFURA_PROJECT_ID")

# Setup logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# Initialize Web3
w3 = Web3(Web3.HTTPProvider(INFURA_URL))

# Token contract addresses
USDT_ADDRESS = Web3.to_checksum_address("0xdAC17F958D2ee523a2206206994597C13D831ec7")
USDC_ADDRESS = Web3.to_checksum_address("0xA0b86991C6218b36c1d19D4a2e9Eb0cE3606eb48")

# ERC20 ABI (only the needed methods)
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function",
    },
]

# Token contract instances
usdt = w3.eth.contract(address=USDT_ADDRESS, abi=ERC20_ABI)
usdc = w3.eth.contract(address=USDC_ADDRESS, abi=ERC20_ABI)

# Parse and clean address list
def extract_addresses(text: str):
    return re.findall(r"0x[a-fA-F0-9]{40}", text)[:10]

# Format balance with decimals
def get_token_balance(contract, address):
    balance = contract.functions.balanceOf(address).call()
    decimals = contract.functions.decimals().call()
    return Decimal(balance) / (10 ** decimals)

# Handle /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send up to 10 Ethereum addresses and I'll return their ETH, USDT, and USDC balances.")

# Handle message with addresses
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    addresses = extract_addresses(update.message.text)
    if not addresses:
        await update.message.reply_text("Please send up to 10 valid Ethereum addresses.")
        return

    results = []
    for addr in addresses:
        try:
            eth_balance = w3.eth.get_balance(addr) / 10**18
            usdt_balance = get_token_balance(usdt, addr)
            usdc_balance = get_token_balance(usdc, addr)
            results.append(
                f"{addr}\n  ETH: {eth_balance:.4f}\n  USDT: {usdt_balance:.2f}\n  USDC: {usdc_balance:.2f}"
            )
        except Exception as e:
            results.append(f"{addr}\n  Error: {str(e)}")

    reply = "\n\n".join(results)
    await update.message.reply_text(reply)

# Main entry
async def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🤖 Bot is polling...")
    await app.run_polling()

# Workaround to avoid "event loop already running" error
if __name__ == "__main__":
    import asyncio

    try:
        asyncio.get_event_loop().run_until_complete(main())
    except RuntimeError as e:
        if "already running" in str(e):
            loop = asyncio.get_event_loop()
            loop.create_task(main())
        else:
            raise
