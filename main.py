import os
import csv
import asyncio
from io import StringIO
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from web3 import Web3
from dotenv import load_dotenv
import nest_asyncio

# Load environment variables
load_dotenv()

# Required environment variables
BOT_TOKEN = os.getenv("7624939968:AAGpQN-YToHmMWxMEUerS5PzNeNqs29wGTg")
INFURA_URL = os.getenv("https://eth-mainnet.g.alchemy.com/v2/HZOmTXoCl7ZG7tgzp3D8DrmvJn0NlNrK")

# Setup
w3 = Web3(Web3.HTTPProvider(INFURA_URL))
nest_asyncio.apply()

# ERC-20 contract ABIs (simplified balanceOf)
ERC20_ABI = [{"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"}]

# Common stablecoin addresses
TOKENS = {
    "ETH": None,
    "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
    "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = (
        "This bot will query ETH, USDT, USDC balances from the chain.\n"
        "If you enter 10 or fewer addresses, the bot will return the results in chat.\n"
        "You can paste up to 100 addresses line by line to have a CSV file returned."
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

        # Token balances
        for symbol, token_address in TOKENS.items():
            if token_address is None:
                continue
            contract = w3.eth.contract(address=Web3.to_checksum_address(token_address), abi=ERC20_ABI)
            balance = contract.functions.balanceOf(Web3.to_checksum_address(address)).call()
            decimals = 6 if symbol == "USDT" else 6 if symbol == "USDC" else 18
            balances[symbol] = balance / (10 ** decimals)
    except Exception as e:
        balances = {"ETH": "Error", "USDT": "Error", "USDC": "Error"}
    return balances

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
            replies.append(f"{address[:6]}...{address[-4:]}\nETH: {balances['ETH']:.6f} | USDT: {balances['USDT']:.2f} | USDC: {balances['USDC']:.2f}")
        await update.message.reply_text("\n\n".join(replies))
    elif len(addresses) <= 100:
        await update.message.reply_text("Querying balances and generating CSV...")
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["Address", "ETH", "USDT", "USDC"])
        for address in addresses:
            balances = await get_balances(address)
            writer.writerow([address, balances['ETH'], balances['USDT'], balances['USDC']])
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
