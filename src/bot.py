import json
import typing
import discord
import asyncio
from constants.candy_tier import CandyTier
from database import Database
from services.dashboard_service import DashboardService
from services.team_service import TeamService
from discord.ext import commands
from discord import Enum, app_commands
from enum import Enum

class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        intents = discord.Intents.all()
        intents.message_content = True

        super().__init__(command_prefix="!", intents=intents, *args, **kwargs)

        # Services
        self.database = Database()
        self.dashboard_service = DashboardService()
        self.teams_service = TeamService()

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

@bot.tree.command(name="myteam", description="Team")
async def my_team(interaction: discord.Interaction):
    team = await bot.teams_service.get_team_from_channel_id(interaction, bot.database)
    if team is None:
        await interaction.response.send_message("No team info found")
    await interaction.response.send_message(f"```{team.name, team.channel_id, team.members}```")

@bot.tree.command(name="submit", description="Submit a drop!")
async def submit(interaction: discord.Interaction, tier: CandyTier.CANDYTIER):
    team = await bot.teams_service.get_team_from_channel_id(interaction, bot.database)
    if team is None:
        await interaction.response.send_message("No team info found")

    await interaction.channel.send(f"Generating a new {tier.name} candy bar task")
    task = await bot.teams_service.assign_task(team, tier, bot.database, bot.dashboard_service)
    
@bot.tree.command(name="random_dashboard", description="[TESTING ONLY] Generates a random dashboard for testing")
async def random_dashboard(interaction: discord.Interaction):
    await interaction.channel.send(content = "Randomly generated board", file = await bot.dashboard_service.generate_board())
    
@bot.tree.command(name="all_teams", description="[TESTING ONLY] Get all teams")
async def get_all_teams(interaction: discord.Interaction):
    await bot.teams_service.get_all_teams(interaction, bot.database)

# Main function to start the bot
async def main():
    await bot.start(bot.bot_token)

if __name__ == "__main__":
    asyncio.run(main())
