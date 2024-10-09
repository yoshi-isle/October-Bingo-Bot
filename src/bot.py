import json
import discord
import asyncio
from services.dashboard_service import DashboardService
from discord.ext import commands
from discord import app_commands

class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        intents = discord.Intents.all()
        intents.message_content = True

        super().__init__(command_prefix="!", intents=intents, *args, **kwargs)

        # Services
        self.dashboard_service = DashboardService()

        # Load bot token and public key from configuration
        with open('appSettings.local.json', 'r') as file:
            data = json.load(file)

        self.bot_token = data["bot"]["token"]
        self.public_key = data["bot"]["publickey"]

    # Sync slash commands when the bot is ready
    async def setup_hook(self):
        await self.tree.sync() 

    async def on_ready(self):
        print(f'Bot is ready! Logged in as {self.user}')

bot = Bot()

# Slash Commands
@bot.tree.command(name="ping", description="Responds with pong.")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("pong")

@bot.tree.command(name="dashboard1", description="Posts the BG for dashboard")
async def dashboard1(interaction: discord.Interaction):
    await bot.dashboard_service.post_empty_dashboard(interaction)

@bot.tree.command(name="random_dashboard", description="Generates a random dashboard for testing")
async def random_dashboard(interaction: discord.Interaction):
    await interaction.response.send_message("Generating random board")
    await bot.dashboard_service.generate_random_board(interaction)

# Main function to start the bot
async def main():
    await bot.start(bot.bot_token)

if __name__ == "__main__":
    asyncio.run(main())
