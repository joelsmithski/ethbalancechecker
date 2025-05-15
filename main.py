import os
import csv
import asyncio
from io import StringIO
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from web3 import Web3
from dotenv import load_dotenv
import nest_asyncio

# Load environment variables from .env file
load_dotenv()

# ======= ADD YOUR BOT TOKEN AND INFURA URL IN YOUR .env FILE =======
# Example:
# BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
# INFURA_URL=https://mainnet.infura.io/v3/YOUR_INFURA_PROJECT_ID
BOT_TOKEN = os.getenv("BOT_TOKEN")
INFURA_URL = os.getenv("INFURA_URL")

if not BOT_TOKEN or not INFURA_URL:
    raise ValueError("Missing BOT_TOKEN or INFURA_URL in environment variables.")

# Setup Web3
w3 = Web3(Web3.HTTPProvider(INFURA_URL))

# Apply nest_asyncio to allow asyncio event loop re-entry (needed for some environments)
nest_asyncio.apply()

# ERC-20 contract ABI snippet to read balanceOf
ERC20_ABI = [{
    "constant": True,
    "inputs": [{"name": "_owner", "type": "address"}],
    "name": "balanceOf",
    "outputs": [{"name": "balance", "type": "uint256"}],
    "type": "function"
}]

# Token contract addresses on Ethereum mainnet
TOKENS = {
    "ETH": None,  # Native ETH balance
    "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
    "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = (
        "This bot will query ETH, USDT, USDC balances from the Ethereum blockchain.\n"
        "If you send 10 or fewer addresses, results will appear in chat.\n"
        "If you send 11 to 100 addresses (one per line), you will get a CSV file with balances."
    )
    await update.message.reply_text(message)

def is_valid_address(address: str) -> bool:
    return w3.is_address(address)

async def get_balances(address: str) -> dict:
    balances = {}
    try:
        # ETH balance
        eth_balance = w3.eth.get_balance(address)
        balances["ETH"] = w3.from_wei(eth_balance, 'ether')

        # ERC-20 token balances
        for symbol, token_address in TOKENS.items():
            if token_address is None:
                continue
            contract = w3.eth.contract(address=Web3.to_checksum_address(token_address), abi=ERC20_ABI)
            balance = contract.functions.balanceOf(Web3.to_checksum_address(address)).call()
            decimals = 6 if symbol in ["USDT", "USDC"] else 18
            balances[symbol] = balance / (10 ** decimals)
    except Exception as e:
        # On error, mark all balances as "Error"
        balances = {"ETH": "Error", "USDT": "Error", "USDC": "Error"}
    return balances

def format_balance(val, decimals=6):
    try:
        return f"{float(val):.{decimals}f}"
    except Exception:
        return str(val)  # Could be "Error" or other string

async def handle_addresses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    addresses = list({line.strip() for line in text.splitlines() if is_valid_address(line.strip())})

    if not addresses:
        await update.message.reply_text("Please send valid Ethereum addresses.")
        return

    if len(addresses) <= 10:
        await update.message.reply_text("Querying balances...")
        replies = []
        for address in addresses:
            balances = await get_balances(address)
            replies.append(
                f"{address[:6]}...{address[-4:]}\n"
                f"ETH: {format_balance(balances['ETH'], 6)} | "
                f"USDT: {format_balance(balances['USDT'], 2)} | "
                f"USDC: {format_balance(balances['USDC'], 2)}"
            )
        await update.message.reply_text("\n\n".join(replies))

    elif len(addresses) <= 100:
        await update.message.reply_text("Querying balances and generating CSV...")
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["Address", "ETH", "USDT", "USDC"])
        for address in addresses:
            balances = await get_balances(address)
            writer.writerow([
                address,
                format_balance(balances['ETH'], 6),
                format_balance(balances['USDT'], 2),
                format_balance(balances['USDC'], 2)
            ])
        output.seek(0)
        await update.message.reply_document(InputFile(output, filename="balances.csv"))
    else:
        await update.message.reply_text("Please send 100 or fewer addresses.")

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_addresses))

    print("🤖 Bot is polling...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
