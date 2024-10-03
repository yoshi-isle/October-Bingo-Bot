import json
import discord
import asyncio
from discord.ext import commands
from discord import app_commands

# Load bot token and public key from configuration
with open('appSettings.local.json', 'r') as file:
    data = json.load(file)

bot_token = data["bot"]["token"]
public_key = data["bot"]["publickey"]

# Define the bot with appropriate intents
intents = discord.Intents.all()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Define the tree for app commands
tree = bot.tree

@bot.event
async def on_ready():
    print(f'Bot is ready! Logged in as {bot.user}')
    try:
        # Sync slash commands to the server
        await tree.sync()
        print("Slash commands synced.")
    except Exception as e:
        print(f"Error syncing commands: {e}")

# Define a slash command
@tree.command(name="ping", description="Responds with pong.")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("pong")

# Main function to start the bot
async def main():
    await bot.start(bot_token)

if __name__ == "__main__":
    asyncio.run(main())
