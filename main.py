import logging
import os
import asyncio
import csv
import tempfile
from telegram import Update, InputFile
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from web3 import Web3

# === INSERT YOUR BOT TOKEN AND INFURA URL HERE ===
BOT_TOKEN = "7624939968:AAGpQN-YToHmMWxMEUerS5PzNeNqs29wGTg"
INFURA_URL = "https://eth-mainnet.g.alchemy.com/v2/HZOmTXoCl7ZG7tgzp3D8DrmvJn0NlNrK"

# === SETUP ===
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
w3 = Web3(Web3.HTTPProvider(INFURA_URL))

# ERC-20 token addresses (mainnet)
USDT_CONTRACT = w3.to_checksum_address("0xdAC17F958D2ee523a2206206994597C13D831ec7")
USDC_CONTRACT = w3.to_checksum_address("0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606EB48")

# Minimal ABI for balanceOf function
ERC20_ABI = [{"constant":True,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}]
usdt_contract = w3.eth.contract(address=USDT_CONTRACT, abi=ERC20_ABI)
usdc_contract = w3.eth.contract(address=USDC_CONTRACT, abi=ERC20_ABI)


def is_valid_eth_address(addr):
    return w3.is_address(addr)


def fetch_balances(address):
    try:
        address = w3.to_checksum_address(address)
        eth = w3.eth.get_balance(address) / 1e18
        usdt = usdt_contract.functions.balanceOf(address).call() / 1e6
        usdc = usdc_contract.functions.balanceOf(address).call() / 1e6
        return round(eth, 6), round(usdt, 2), round(usdc, 2)
    except Exception as e:
        return f"Error: {e}", "-", "-"


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    input_text = update.message.text
    addresses = list({line.strip() for line in input_text.splitlines() if is_valid_eth_address(line.strip())})

    if not addresses:
        await update.message.reply_text("No valid Ethereum addresses found in your message.")
        return

    results = []
    for addr in addresses:
        eth, usdt, usdc = fetch_balances(addr)
        results.append({"address": addr, "ETH": eth, "USDT": usdt, "USDC": usdc})

    if len(addresses) <= 10:
        response = "\n".join([f"{r['address'][:6]}...{r['address'][-4:]} | ETH: {r['ETH']} | USDT: {r['USDT']} | USDC: {r['USDC']}" for r in results])
        await update.message.reply_text(response)
    else:
        with tempfile.NamedTemporaryFile(mode="w", delete=False, newline="", suffix=".csv") as csvfile:
            fieldnames = ["Address", "ETH", "USDT", "USDC"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for r in results:
                writer.writerow({"Address": r['address'], "ETH": r['ETH'], "USDT": r['USDT'], "USDC": r['USDC']})
            csv_path = csvfile.name

        with open(csv_path, "rb") as f:
            await update.message.reply_document(InputFile(f, filename="balances.csv"))
        os.remove(csv_path)


async def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    await app.run_polling()


if __name__ == "__main__":
    asyncio.run(main())
