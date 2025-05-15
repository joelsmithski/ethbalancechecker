from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from web3 import Web3
import os

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ETH_NODE_URL = os.getenv("ETH_NODE_URL")

USDT = Web3.to_checksum_address('0xdAC17F958D2ee523a2206206994597C13D831ec7')
USDC = Web3.to_checksum_address('0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606EB48')

ERC20_ABI = [{"constant":True,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}]

w3 = Web3(Web3.HTTPProvider(ETH_NODE_URL))
usdt_contract = w3.eth.contract(address=USDT, abi=ERC20_ABI)
usdc_contract = w3.eth.contract(address=USDC, abi=ERC20_ABI)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Paste Ethereum addresses separated by commas or new lines.")

async def check_balances(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    addresses = [line.strip() for line in text.replace(",", "\n").splitlines()]
    results = []

    for addr in addresses:
        if w3.is_address(addr):
            addr = Web3.to_checksum_address(addr)
            eth_balance = w3.eth.get_balance(addr) / 1e18
            usdt_balance = usdt_contract.functions.balanceOf(addr).call() / 1e6
            usdc_balance = usdc_contract.functions.balanceOf(addr).call() / 1e6
            results.append(f"{addr}:\n  ETH: {eth_balance:.4f}\n  USDT: {usdt_balance:.2f}\n  USDC: {usdc_balance:.2f}\n")
        else:
            results.append(f"{addr} is not a valid address.")

    await update.message.reply_text("\n".join(results))

app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), check_balances))

app.run_polling()