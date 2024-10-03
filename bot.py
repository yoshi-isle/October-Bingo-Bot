import json
import discord
from discord.ext import commands

with open('appSettings.local.json', 'r') as file:
    data = json.load(file)

bot_token = data["bot"]["token"]
public_key = data["bot"]["publickey"]

# Define the bot
intents = discord.Intents.all()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'Bot is ready! Logged in as {bot.user}')

async def main():
    await bot.start(bot_token)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
