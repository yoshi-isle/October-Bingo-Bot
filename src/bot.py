import json
import discord
import asyncio
from constants.candy_tier import CandyTier
from database import Database, Team
from services.dashboard_service import DashboardService
from services.embed_generator import EmbedGenerator
from services.team_service import TeamService
from discord.ext import commands
from discord import app_commands
class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        intents = discord.Intents.all()
        intents.message_content = True

        super().__init__(command_prefix="!", intents=intents, *args, **kwargs)

        # Services
        self.database = Database()
        self.dashboard_service = DashboardService()
        self.teams_service = TeamService()
        self.embed_generator = EmbedGenerator()

        # Load bot token and public key from configuration
        with open('appSettings.local.json', 'r') as file:
            data = json.load(file)

        self.bot_token = data["bot"]["token"]
        self.public_key = data["bot"]["publickey"]
        self.submit_channel_id = data["channels"]["submit"]

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

@bot.tree.command(name="board", description="Your team's board")
async def my_team(interaction: discord.Interaction):
    try:
        team = await bot.teams_service.get_team_from_channel_id(interaction.channel_id, bot.database)
        print(team)
        if team is None:
            await interaction.response.send_message("No team info found")
            return
        await interaction.channel.send(file = await bot.dashboard_service.generate_board(team))
        await interaction.channel.send(embed = await bot.embed_generator.make_team_embed(team))
    except Exception as e:
        print(e)

@bot.tree.command(name="submit", description="Submit a drop!")
async def submit(interaction: discord.Interaction, tier: CandyTier.CANDYTIER, image: discord.Attachment):
    try:
        submit_channel = bot.get_channel(bot.submit_channel_id)
        if interaction.channel.id != bot.submit_channel_id:
                await interaction.response.send_message(f"Wrong channel. Please go to {submit_channel.mention}")
                return

        team, info = await bot.teams_service.get_team_from_user_id(str(interaction.user.id), bot.database)
        if team is None:
            await interaction.response.send_message(f"No team info found for you. Please contact <@726237123857874975>")
            return
        
        await interaction.response.send_message(f"Thank your for your submission. Your board will be updated shortly in {bot.get_channel(int(team.channel_id)).mention}", ephemeral=True)
        await bot.teams_service.assign_task(team, tier, bot.database, bot.dashboard_service)        
        await interaction.channel.send(f"{interaction.user.mention} submitted for {team.name}.\n {info[tier.name][0]['Name']}", file=await image.to_file())
    except Exception as e:
        print(e)
    # await interaction.channel.send(file = await bot.dashboard_service.generate_board(updated_team))
    
@bot.tree.command(name="initialize_team", description="Create a team record in the database from this channel")
@app_commands.checks.has_permissions(administrator=True)
async def initialize_team(interaction: discord.Interaction):
    team = await bot.teams_service.initialize_team(interaction.channel.name, interaction.channel_id, bot.database, bot.dashboard_service)
    await interaction.channel.send(file = await bot.dashboard_service.generate_board(team))
    await interaction.response.send_message(f"Created team!")

@initialize_team.error
async def get_all_teams_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)

@bot.tree.command(name="all_teams", description="[TESTING ONLY] Get all teams")
async def get_all_teams(interaction: discord.Interaction):
    await bot.teams_service.get_all_teams(interaction, bot.database)

# Main function to start the bot
async def main():
    await bot.start(bot.bot_token)

if __name__ == "__main__":
    asyncio.run(main())
