import json
from bson import ObjectId
import discord
import asyncio
from constants.candy_tier import CandyTier
from database import Database, Team
from services.dashboard_service import DashboardService
from services.embed_generator import EmbedGenerator
from services.team_service import TeamService
from discord.ext import commands
from discord import app_commands, Message
from discord.ext import tasks
from datetime import datetime, timedelta

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
        self.leaderboard_message_id = data["bot"]["leaderboard_message_id"]
        self.leaderboard_channel_id = data["bot"]["leaderboard_channel_id"]
        self.changelog_channel_id = data["bot"]["changelog_channel_id"]

    # Sync slash commands when the bot is ready
    async def setup_hook(self):
        await self.tree.sync() 

    async def on_ready(self):
        print(f'Bot is ready! Logged in as {self.user}')
        check_bucket_expiry.start()
        update_leaderboard.start()

bot = Bot()
    
# Slash Commands
@bot.tree.command(name="board", description="Your team's board")
async def my_team(interaction: discord.Interaction):
    try:
        team = await bot.teams_service.get_team_from_channel_id(interaction.channel_id, bot.database)
        if team is None:
            await interaction.response.send_message("Please use this command in your team's channel")
            return
        
        if team.updating:
            await interaction.response.send_message(f"Your team's board is currently being updated. Please wait ~30 seconds.", ephemeral=True)
            return
        
        await interaction.response.send_message("Grabbing your latest board", ephemeral=True)
        dashboard_service = DashboardService()
        message = await interaction.channel.send(file = await dashboard_service.generate_board(team))
        await interaction.channel.send(embed = await bot.embed_generator.make_team_embed(team))
        
        # Pin new board to channel
        pins: list[Message] = await interaction.channel.pins()
        for pin in range(len(pins)):
            await pins[pin].unpin(reason=None)
        await message.pin(reason=None)     
                    
    except Exception as e:
        print("Error with /board command", e)
        
@bot.tree.command(name="submit", description="Submit a drop!")
async def submit(interaction: discord.Interaction, tier: CandyTier.CANDYTIER, image: discord.Attachment):
    try:
        submit_channel = bot.get_channel(bot.submit_channel_id)
        if interaction.channel.id != bot.submit_channel_id:
                await interaction.response.send_message(f"Wrong channel. Please go to {submit_channel.mention}")
                return

        team, info = await bot.teams_service.get_team_from_user_id(str(interaction.user.id), bot.database)
        if team is None:
            await interaction.response.send_message(f"No team information was found for you. Please contact <@726237123857874975>", ephemeral=True)
            return

        if team.updating:
            await interaction.response.send_message(f"Your team's board is already being updated. Please wait ~30 seconds.", ephemeral=True)
            return
        
        # Check to ensure bucket or not
        if tier == CandyTier.CANDYTIER["Candy-bucket"] and not team.bucket_task:
            await interaction.response.send_message(f"You don't have a candy bucket. Wrong option maybe?", ephemeral=True)
            return
        
        await interaction.response.send_message(f"Thank your for your submission. Your board will be updated shortly in {bot.get_channel(int(team.channel_id)).mention}", ephemeral=True)
        await bot.teams_service.award_points(team, bot.database, tier)
        
        # Updating team
        await bot.teams_service.updating_team(team, bot.database, True)
        
        # Wait 15 and update team board
        await asyncio.sleep(15)
        
        # Show changelog        
        changelog_channel = bot.get_channel(int(bot.changelog_channel_id))
        await changelog_channel.send(f"{interaction.user.mention} completed a tile for {team.name}.\n {info[tier.name][0]['Description']}", file=await image.to_file())
        
        team = await bot.teams_service.assign_task(team, tier, bot.database, bot.dashboard_service, True)
        team_channel = bot.get_channel(int(team.channel_id))
        dashboard_service = DashboardService()
        message: Message = await team_channel.send(file = await dashboard_service.generate_board(team))
        await team_channel.send(embed = await bot.embed_generator.make_team_embed(team))
        
        # Pin new board to channel
        pins: list[Message] = await team_channel.pins()
        for pin in range(len(pins)):
            await pins[pin].unpin(reason=None)
        await message.pin(reason=None)
            
         # Updating team
        await bot.teams_service.updating_team(team, bot.database, False)
        
    except Exception as e:
        print("Error with /submit command", e)
        await bot.teams_service.updating_team(team, bot.database, False)

@bot.tree.command(name="reroll", description="Re-roll a slot")
async def reroll(interaction: discord.Interaction, tier: CandyTier.CANDYTIER):
    try:
        team = await bot.teams_service.get_team_from_channel_id(interaction.channel_id, bot.database)
        if team is None:
            await interaction.response.send_message("Please use this command in your team's channel", ephemeral = True)
            return
        
        if team.updating:
            await interaction.response.send_message(f"Your team's board is currently being updated. Please wait ~30 seconds.", ephemeral=True)
            return

        # Check to ensure bucket or not
        if tier == CandyTier.CANDYTIER["Candy-bucket"]:
            await interaction.response.send_message(f"You can't re-roll a candy bucket.", ephemeral=True)
            return
        
        reroll = await bot.teams_service.reroll_task(team, tier, bot.database, bot.dashboard_service)
        
        if reroll:
            await interaction.response.send_message(f"{interaction.user.mention} is re-rolling the {tier.name} slot for the team!")
            team = await bot.teams_service.get_team_from_channel_id(interaction.channel_id, bot.database)
            dashboard_service = DashboardService()
            message = await interaction.channel.send(file = await dashboard_service.generate_board(team))
            await interaction.channel.send(embed = await bot.embed_generator.make_team_embed(team))
            
            # Pin new board to channel
            pins: list[Message] = await interaction.channel.pins()
            for pin in range(len(pins)):
                await pins[pin].unpin(reason=None)
            await message.pin(reason=None)
            
        else:
            await interaction.response.send_message("Your team cannot re-roll that slot yet.")
        
    except Exception as e:
        print("Error with /reroll command", e)

@bot.tree.command(name="initialize_team", description="Create a team record in the database from this channel")
@app_commands.checks.has_permissions(administrator=True)
async def initialize_team(interaction: discord.Interaction):
    team = await bot.teams_service.initialize_team(interaction.channel.name, interaction.channel_id, bot.database, bot.dashboard_service)
    await interaction.response.send_message(f"Created team!", ephemeral=True)
    await interaction.channel.send(file = await bot.dashboard_service.generate_board(team))
    await interaction.channel.send(embed = await bot.embed_generator.make_team_embed(team))

@initialize_team.error
async def get_all_teams_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)

@bot.tree.command(name="leaderboard", description="Top teams leaderboard")
@app_commands.checks.has_permissions(administrator=True)
async def leaderboard(interaction: discord.Interaction):
    try:
        teams = await bot.teams_service.get_all_teams(bot.database)
        await interaction.channel.send(embed = await bot.embed_generator.make_topteams_embed(teams))
    except Exception as e:
        print("Error with /leaderboard command", e)

@tasks.loop(minutes=5)
async def update_leaderboard():
    try:
        channel = bot.get_channel(int(bot.leaderboard_channel_id))
        leaderboard_message = await channel.fetch_message(int(bot.leaderboard_message_id))

        teams = await bot.teams_service.get_all_teams(bot.database)
        embed = await bot.embed_generator.make_topteams_embed(teams)

        current_time = datetime.now() + timedelta(minutes=5)
        discord_timestamp = f"<t:{int(current_time.timestamp())}:R>"

        embed.description += f"\n\nNext update {discord_timestamp}"

        await leaderboard_message.edit(embed=embed)
    except Exception as e:
        print("Error with update_leaderboard timer", e)

@tasks.loop(minutes=30)
async def check_bucket_expiry():
    try:
        # Fetch all teams from the database
        teams = await bot.teams_service.get_all_teams(bot.database)
        current_time = datetime.now()

        for team in teams:
            if "Candy-bucket" in team and team["Candy-bucket"]:
                if current_time > team["Candy-bucket"][1]:
                    team = bot.database.teams_collection.find_one_and_update(
                        {"_id": ObjectId(team["_id"])},
                        {"$set": {"Candy-bucket": []}}
                    )
                    updated_team = Team(
                        _id=team.get("_id", ""),
                        name=team.get("Name", ""),
                        members=team.get("Members", []),
                        points=team.get("Points", 0),
                        channel_id=team.get("ChannelId", ""),
                        mini_task=team.get("Mini-sized", ""),
                        fun_task=team.get("Fun-sized", ""),
                        full_task=team.get("Full-sized", ""),
                        family_task=team.get("Family-sized", ""),
                        bucket_task=None,
                        submission_history=team.get("SubmissionHistory", ""),
                        updating=team.get("Updating", ""))
                    team_channel = bot.get_channel(int(updated_team.channel_id))
                    await team_channel.send("## Your Candy-bucket task has expired.")
                    dashboard_service = DashboardService()
                    message = await team_channel.send(file = await dashboard_service.generate_board(updated_team))
                    await team_channel.send(embed = await bot.embed_generator.make_team_embed(updated_team))
                    
                    # Pin new board to channel
                    pins: list[Message] = await team_channel.pins()
                    for pin in range(len(pins)):
                        await pins[pin].unpin(reason=None)
                    await message.pin(reason=None)
                    
    except Exception as e:
        print("Error with check_bucket_expiry timer", e)

# Main function to start the bot
async def main():
    await bot.start(bot.bot_token)

if __name__ == "__main__":
    asyncio.run(main())
