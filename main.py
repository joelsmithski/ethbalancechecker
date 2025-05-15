import logging
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from web3 import Web3

# 🚨 REQUIRED: Paste your actual bot token from @BotFather below
BOT_TOKEN = "7624939968:AAGpQN-YToHmMWxMEUerS5PzNeNqs29wGTg"

# 🚨 REQUIRED: Paste your actual Infura or Alchemy HTTP endpoint below
INFURA_URL = "https://eth-mainnet.g.alchemy.com/v2/HZOmTXoCl7ZG7tgzp3D8DrmvJn0NlNrK"

# Initialize Web3
web3 = Web3(Web3.HTTPProvider(INFURA_URL))

# ERC20 token contract addresses
USDT_CONTRACT = Web3.to_checksum_address("0xdAC17F958D2ee523a2206206994597C13D831ec7")
USDC_CONTRACT = Web3.to_checksum_address("0xA0b86991C6218b36c1d19D4a2e9Eb0cE3606eB48")

# Minimal ABI for ERC-20 balanceOf
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function",
    }
]

# Initialize token contracts
usdt_contract = web3.eth.contract(address=USDT_CONTRACT, abi=ERC20_ABI)
usdc_contract = web3.eth.contract(address=USDC_CONTRACT, abi=ERC20_ABI)

logging.basicConfig(level=logging.INFO)

# /start handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send me up to 10 Ethereum addresses separated by spaces or new lines.")

# Clean and extract up to 10 addresses
def extract_addresses(text):
    return [line.strip() for line in text.replace(",", "\n").splitlines() if web3.is_address(line.strip())][:10]

# Query ETH + stablecoin balances
def get_balances(addresses):
    results = []
    for address in addresses:
        addr = Web3.to_checksum_address(address)
        eth = web3.eth.get_balance(addr) / 1e18
        usdt = usdt_contract.functions.balanceOf(addr).call() / 1e6
        usdc = usdc_contract.functions.balanceOf(addr).call() / 1e6
        results.append(f"{addr}:\n  ETH: {eth:.6f}\n  USDT: {usdt:.2f}\n  USDC: {usdc:.2f}")
    return "\n\n".join(results)

# Message handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    addresses = extract_addresses(update.message.text)
    if not addresses:
        await update.message.reply_text("No valid Ethereum addresses found.")
        return
    balances = await asyncio.to_thread(get_balances, addresses)
    await update.message.reply_text(balances)

# Main app logic
async def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🤖 Bot is polling...")
    await app.run_polling()

# Run bot
if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
