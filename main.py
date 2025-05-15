import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from web3 import Web3

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
INFURA_URL = os.getenv("INFURA_URL")

w3 = Web3(Web3.HTTPProvider(INFURA_URL))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Send me an Ethereum address to get the ETH, USDT, and USDC balances.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    address = update.message.text
    if not w3.is_address(address):
        await update.message.reply_text("Invalid Ethereum address.")
        return

    try:
        eth_balance = w3.eth.get_balance(address) / 10**18
    except Exception as e:
        eth_balance = f"Error: {e}"

    try:
        usdt_contract = w3.eth.contract(
            address=w3.to_checksum_address("0xdAC17F958D2ee523a2206206994597C13D831ec7"),
            abi=[
                {
                    "constant": True,
                    "inputs": [{"name": "_owner", "type": "address"}],
                    "name": "balanceOf",
                    "outputs": [{"name": "balance", "type": "uint256"}],
                    "type": "function",
                }
            ]
        )
        usdt_balance = usdt_contract.functions.balanceOf(address).call() / 10**6
    except Exception as e:
        usdt_balance = f"Error: {e}"

    try:
        usdc_contract = w3.eth.contract(
            address=w3.to_checksum_address("0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"),
            abi=[
                {
                    "constant": True,
                    "inputs": [{"name": "_owner", "type": "address"}],
                    "name": "balanceOf",
                    "outputs": [{"name": "balance", "type": "uint256"}],
                    "type": "function",
                }
            ]
        )
        usdc_balance = usdc_contract.functions.balanceOf(address).call() / 10**6
    except Exception as e:
        usdc_balance = f"Error: {e}"

    await update.message.reply_text(
        f"ETH: {eth_balance}\nUSDT: {usdt_balance}\nUSDC: {usdc_balance}"
    )

app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", start))
app.add_handler(CommandHandler("balance", handle_message))
app.add_handler(CommandHandler("check", handle_message))
app.add_handler(CommandHandler("query", handle_message))
app.add_handler(CommandHandler("eth", handle_message))
app.add_handler(CommandHandler("usdt", handle_message))
app.add_handler(CommandHandler("usdc", handle_message))

from telegram.ext import MessageHandler, filters
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# ⬇️ This is the webhook-based runner for Render
import asyncio

if __name__ == "__main__":
    async def main():
        await app.initialize()
        await app.start()
        await app.updater.start_webhook(
            listen="0.0.0.0",
            port=int(os.environ.get("PORT", 8080)),
            url_path=TELEGRAM_BOT_TOKEN,
            webhook_url=f"https://{os.environ['RENDER_EXTERNAL_HOSTNAME']}/{TELEGRAM_BOT_TOKEN}"
        )
        await app.updater.idle()

    asyncio.run(main())
