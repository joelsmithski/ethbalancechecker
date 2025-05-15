import os
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from web3 import Web3

# 🔐 Insert your secrets here
BOT_TOKEN = "7624939968:AAGpQN-YToHmMWxMEUerS5PzNeNqs29wGTg"
INFURA_URL = "https://eth-mainnet.g.alchemy.com/v2/HZOmTXoCl7ZG7tgzp3D8DrmvJn0NlNrK"

# Setup web3 connection
web3 = Web3(Web3.HTTPProvider(INFURA_URL))

# ERC20 ABI fragment
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
    }
]

# ERC20 token addresses
TOKENS = {
    "ETH": None,
    "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
    "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Send me up to 10 Ethereum addresses (separated by spaces or newlines), and I’ll fetch their ETH, USDT, and USDC balances.")


async def handle_addresses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw_text = update.message.text.strip()
    addresses = raw_text.replace(',', ' ').replace('\n', ' ').split()
    addresses = [addr for addr in addresses if web3.is_address(addr)]

    if len(addresses) == 0:
        await update.message.reply_text("❌ Please send at least one valid Ethereum address.")
        return
    if len(addresses) > 10:
        await update.message.reply_text("❌ You can only check up to 10 addresses at a time.")
        return

    results = []
    for addr in addresses:
        balances = []
        # ETH
        eth_balance = web3.eth.get_balance(addr)
        balances.append(f"ETH: {web3.from_wei(eth_balance, 'ether'):.6f}")

        # Tokens
        for token_name, token_addr in TOKENS.items():
            if token_name == "ETH":
                continue
            contract = web3.eth.contract(address=token_addr, abi=ERC20_ABI)
            try:
                balance = contract.functions.balanceOf(addr).call()
                decimals = contract.functions.decimals().call()
                adjusted = balance / (10 ** decimals)
                balances.append(f"{token_name}: {adjusted:.2f}")
            except Exception as e:
                balances.append(f"{token_name}: error")

        result = f"📍 `{addr}`\n" + "\n".join(balances)
        results.append(result)

    await update.message.reply_text("\n\n".join(results), parse_mode="Markdown")


async def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_addresses))

    print("🤖 Bot is polling...")
    await app.run_polling()


if __name__ == "__main__":
    asyncio.run(main())
