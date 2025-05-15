import os
import csv
import tempfile
import asyncio
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from web3 import Web3

# Insert your bot token and Infura URL here
BOT_TOKEN = "7624939968:AAGpQN-YToHmMWxMEUerS5PzNeNqs29wGTg"
INFURA_URL = "https://eth-mainnet.g.alchemy.com/v2/HZOmTXoCl7ZG7tgzp3D8DrmvJn0NlNrK"

# ERC20 token contract addresses (Ethereum Mainnet)
USDT_CONTRACT = "0xdAC17F958D2ee523a2206206994597C13D831ec7"
USDC_CONTRACT = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"

# ERC20 ABI for balanceOf
ERC20_ABI = [{
    "constant": True,
    "inputs": [{"name": "_owner", "type": "address"}],
    "name": "balanceOf",
    "outputs": [{"name": "balance", "type": "uint256"}],
    "type": "function"
}]

w3 = Web3(Web3.HTTPProvider(INFURA_URL))

usdt_contract = w3.eth.contract(address=USDT_CONTRACT, abi=ERC20_ABI)
usdc_contract = w3.eth.contract(address=USDC_CONTRACT, abi=ERC20_ABI)

async def fetch_balances(address):
    try:
        eth_balance = w3.from_wei(w3.eth.get_balance(address), 'ether')
        usdt_balance = usdt_contract.functions.balanceOf(address).call() / 1e6
        usdc_balance = usdc_contract.functions.balanceOf(address).call() / 1e6
        return (f"{eth_balance:.4f}", f"{usdt_balance:.2f}", f"{usdc_balance:.2f}")
    except Exception:
        return ("error", "error", "error")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "This bot will query ETH, USDT, USDC balances from the chain.\n"
        "If you enter 10 or fewer addresses, the bot will return the results in chat.\n"
        "You can paste up to 100 addresses line by line to receive a CSV file."
    )
    await update.message.reply_text(msg)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_text = update.message.text.strip()
    addresses = [line.strip() for line in message_text.splitlines() if line.strip().startswith("0x") and len(line.strip()) == 42]

    if not addresses:
        await update.message.reply_text("❌ No valid Ethereum addresses found.")
        return

    if len(addresses) > 100:
        await update.message.reply_text("❌ Too many addresses. Please send no more than 100 at a time.")
        return

    results = []
    for address in addresses:
        eth, usdt, usdc = await fetch_balances(address)
        results.append({"Address": address, "ETH": eth, "USDT": usdt, "USDC": usdc})

    if len(results) <= 10:
        response_lines = [f"`{r['Address']}`\n  - ETH: {r['ETH']}\n  - USDT: {r['USDT']}\n  - USDC: {r['USDC']}" for r in results]
        await update.message.reply_text("\n\n".join(response_lines), parse_mode="Markdown")
    else:
        with tempfile.NamedTemporaryFile(mode="w+", suffix=".csv", delete=False) as tmpfile:
            writer = csv.DictWriter(tmpfile, fieldnames=["Address", "ETH", "USDT", "USDC"])
            writer.writeheader()
            writer.writerows(results)
            tmpfile_path = tmpfile.name

        with open(tmpfile_path, "rb") as f:
            await update.message.reply_document(InputFile(f, filename="balances.csv"))

        os.remove(tmpfile_path)

async def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🤖 Bot is polling...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
