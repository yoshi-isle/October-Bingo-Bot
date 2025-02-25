import json
from bson import ObjectId
import discord
import asyncio
from pymongo import ReturnDocument
from constants.candy_tier import CandyTier
from database import Database, Team
from services.dashboard_service import DashboardService
from services.embed_generator import EmbedGenerator
from services.team_service import TeamService
from services.user_sheet_service import UserSheetsService
from discord.ext import commands
from discord import app_commands, Message
from discord.ext import tasks
from datetime import datetime, timedelta
from discord import Embed


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
        self.user_sheet_service = UserSheetsService('src/config/config.json', 'src/config/key.json')
        self.show_points = False

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
        team, info = await bot.teams_service.get_team_from_channel_id(interaction.channel_id, bot.database)
        if team is None:
            await interaction.response.send_message("Please use this command in your team's channel", ephemeral=True)
            return
        
        if team.updating:
            await interaction.response.send_message(f"Your team's board is currently being updated. Please wait ~30 seconds.", ephemeral=True)
            return
        
        await interaction.response.send_message("Grabbing your latest board")
        dashboard_service = DashboardService()
        try:
            message = await interaction.channel.send(file = await dashboard_service.generate_board(team))
            await interaction.channel.send(embed = await bot.embed_generator.make_team_embed(team))

            # Pin new board to channel
            pins: list[Message] = await interaction.channel.pins()
            for pin in range(len(pins)):
                await pins[pin].unpin(reason=None)
            await message.pin(reason=None)     
        except Exception as e:
            await interaction.channel.send("There's an issue with image generation at the moment")
            await interaction.channel.send(embed = await bot.embed_generator.make_team_embed(team))
            print("Error making board", e)
            
        
    except Exception as e:
        print("Error with /board command", e)
        
@bot.tree.command(name="submit", description="Submit a drop!")
async def submit(interaction: discord.Interaction, tier: CandyTier.CANDYTIER, image: discord.Attachment):
    try:
        team, info  = await bot.teams_service.get_team_from_channel_id(interaction.channel_id, bot.database)
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
    
        team_channel = bot.get_channel(int(team.channel_id))
        
        # Subtract CompletionCounter
        info[tier.name][0]["CompletionCounter"] -= 1
        update = bot.database.teams_collection.find_one_and_update(
                        {"_id": ObjectId(team._id)},
                        {"$set": {tier.name: [info[tier.name][0], info[tier.name][1]]}},
                        return_document = ReturnDocument.AFTER
                    )
        if update[tier.name][0]["CompletionCounter"] <= 0:
            # Tile complete past this point
            await interaction.response.send_message(f"**{tier.name}** complete! Your board will be updated shortly.")
            await bot.teams_service.award_points(team, bot.database, tier, interaction.user.name, bot.user_sheet_service, image.url)
            
            # Updating team
            await bot.teams_service.updating_team(team, bot.database, True)
            
            # Wait 15 and update team board
            await asyncio.sleep(15)
            
            # Show changelog        
            changelog_channel = bot.get_channel(int(bot.changelog_channel_id))
            
            embed = Embed(
                title=f"**{team.name}**",
                description=f"{interaction.user.display_name} completed a tile!",
                color=0x00ff00,
            )
            
            embed.set_thumbnail(url=team.image)
            embed.set_image(url=image.url)
            
            await changelog_channel.send(embed = embed)
                                    
            team = await bot.teams_service.assign_task(team, tier, bot.database, bot.dashboard_service, True)
            dashboard_service = DashboardService()
            await team_channel.send("# New board!")

            try:
                message: Message = await team_channel.send(file = await dashboard_service.generate_board(team))
                await team_channel.send(embed = await bot.embed_generator.make_team_embed(team))
                
                # Pin new board to channel
                pins: list[Message] = await team_channel.pins()
                for pin in range(len(pins)):
                    await pins[pin].unpin(reason=None)
                await message.pin(reason=None)    
            except Exception as e:
                await interaction.channel.send("There's an issue with image generation at the moment")
                await team_channel.send(embed = await bot.embed_generator.make_team_embed(team))
                print("Error making board", e)            
                        
            # Updating team
            await bot.teams_service.updating_team(team, bot.database, False)
        else:
            # Tile is not complete yet
            await interaction.response.send_message(f"Thank your for your submission. Your team needs {update[tier.name][0]['CompletionCounter']} more", ephemeral=True)
            embed = Embed(
                title=f"Drop Submission ({tier.name})",
                description=f"{interaction.user.mention} submitted a drop towards **{info[tier.name][0]['Name']}**",
                color=0x00ff00,
            )
            
            embed.set_thumbnail(url=image.url)

            embed.add_field(
                name="Remaining Submissions",
                value=f"Your team needs **{update[tier.name][0]['CompletionCounter']}** more submission(s)"
            )
            
            await team_channel.send(embed = embed)        
            bot.user_sheet_service.add_submission(team.spreadsheet, interaction.user.name, f"Partial: {info[tier.name][0]['Description']}", 0, image.url)
        
    except Exception as e:
        print("Error with /submit command", e)
        await bot.teams_service.updating_team(team, bot.database, False)

@bot.tree.command(name="reroll", description="Re-roll a slot")
async def reroll(interaction: discord.Interaction, tier: CandyTier.CANDYTIER):
    try:
        team, info = await bot.teams_service.get_team_from_channel_id(interaction.channel_id, bot.database)
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
            team, info = await bot.teams_service.get_team_from_channel_id(interaction.channel_id, bot.database)
            dashboard_service = DashboardService()
            
            try:
                message: Message = await interaction.channel.send(file = await dashboard_service.generate_board(team))
                await interaction.channel.send(embed = await bot.embed_generator.make_team_embed(team))
                
                # Pin new board to channel
                pins: list[Message] = await interaction.channel.pins()
                for pin in range(len(pins)):
                    await pins[pin].unpin(reason=None)
                await message.pin(reason=None)    
            except Exception as e:
                await interaction.channel.send("There's an issue with image generation at the moment")
                await interaction.channel.send(embed = await bot.embed_generator.make_team_embed(team))
                print("Error making board", e)            
        
            # Pin new board to channel
            # pins: list[Message] = await interaction.channel.pins()
            # for pin in range(len(pins)):
            #     await pins[pin].unpin(reason=None)
            # await message.pin(reason=None)
            
        else:
            await interaction.response.send_message("Your team cannot re-roll that slot yet.")
        
    except Exception as e:
        print("Error with /reroll command", e)

@bot.tree.command(name="give_bucket", description="Give a team a random bucket")
async def give_bucket(interaction: discord.Interaction):
    try:
        team, info = await bot.teams_service.get_team_from_channel_id(interaction.channel_id, bot.database)
        if team is None:
            await interaction.response.send_message("Please use this command in your team's channel", ephemeral = True)
            return
        
        if team.updating:
            await interaction.response.send_message(f"The team's board is currently being updated. Please wait ~30 seconds.", ephemeral=True)
            return

        if team.bucket_task:
            await interaction.response.send_message(f"This team already has a bucket task", ephemeral=True)
            return
        
        await bot.teams_service.assign_bucket_task(team, bot.database, bot.dashboard_service)
        
        team, info = await bot.teams_service.get_team_from_channel_id(interaction.channel_id, bot.database)
        
        dashboard_service = DashboardService()
            
        try:
            message: Message = await interaction.channel.send(file = await dashboard_service.generate_board(team))
            await interaction.channel.send(embed = await bot.embed_generator.make_team_embed(team))
            
            # Pin new board to channel
            pins: list[Message] = await interaction.channel.pins()
            for pin in range(len(pins)):
                await pins[pin].unpin(reason=None)
            await message.pin(reason=None)    
        except Exception as e:
            await interaction.channel.send("There's an issue with image generation at the moment")
            await interaction.channel.send(embed = await bot.embed_generator.make_team_embed(team))
            print("Error making board", e)

    except Exception as e:
        print("Error giving bucket", e)
        
@bot.tree.command(name="initialize_team", description="Create a team record in the database from this channel")
@app_commands.checks.has_permissions(administrator=True)
async def initialize_team(interaction: discord.Interaction):
    team = await bot.teams_service.initialize_team(interaction.channel.name, interaction.channel_id, bot.database, bot.dashboard_service)
    await interaction.response.send_message(f"Created team!", ephemeral=True)

@initialize_team.error
async def get_all_teams_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)

@bot.tree.command(name="leaderboard", description="Top teams leaderboard")
@app_commands.checks.has_permissions(administrator=True)
async def leaderboard(interaction: discord.Interaction):
    try:
        teams = await bot.teams_service.get_all_teams(bot.database)
        await interaction.channel.send(embed = await bot.embed_generator.make_topteams_embed(teams, False))
    except Exception as e:
        print("Error with /leaderboard command", e)

@bot.tree.command(name="create_sheet", description="Create sheet for team")
@app_commands.checks.has_permissions(administrator=True)
async def create_sheet(interaction: discord.Interaction):
    try:
        team, info  = await bot.teams_service.get_team_from_channel_id(interaction.channel_id, bot.database)
        if team is None:
            await interaction.response.send_message(f"No team information was found for you. Please contact <@726237123857874975>", ephemeral=True)
            return
        
        if team.spreadsheet:
            await interaction.response.send_message(f"There's already a sheet for this team", ephemeral=True)
            return
        
        # Acknowledge the interaction to prevent timeout        
        url = bot.user_sheet_service.create_sheet(interaction.channel.name)
        
        # Send the final response with the sheet URL
        update = bot.database.teams_collection.find_one_and_update(
                        {"_id": ObjectId(team._id)},
                        {"$set": {"Spreadsheet": url}},
                        return_document = ReturnDocument.AFTER
                    )
        print(url)
        
    except Exception as e:
        print("Error with /create_sheet command", e)

@bot.tree.command(name="get_sheet", description="Get sheet for team")
@app_commands.checks.has_permissions(administrator=True)
async def get_sheet(interaction: discord.Interaction):
    try:
        team, info  = await bot.teams_service.get_team_from_channel_id(interaction.channel_id, bot.database)
        if team is None:
            await interaction.response.send_message(f"No team information was found for you. Please contact <@726237123857874975>", ephemeral=True)
            return
        
        await interaction.response.send_message(team.spreadsheet, ephemeral=True)
        
    except Exception as e:
        print("Error with /create_sheet command", e)
        
@bot.tree.command(name="add", description="Add a user to a team")
@app_commands.checks.has_permissions(administrator=True)
async def add_member(interaction: discord.Interaction, user: discord.Member):
    try:
        team, info  = await bot.teams_service.get_team_from_channel_id(interaction.channel_id, bot.database)
        if team is None:
            await interaction.response.send_message(f"No team information was found for you. Please contact <@726237123857874975>", ephemeral=True)
            return
        
        members = team.members or []
        members.append(str(user.id))
        
        update = bot.database.teams_collection.find_one_and_update(
                        {"_id": ObjectId(team._id)},
                        {"$set": {"Members": members}},
                        return_document = ReturnDocument.AFTER
                    )
        
        # teams = await bot.teams_service.get_all_teams(bot.database)
        await interaction.response.send_message(f"Successfully added {user.display_name} ({user.name})", ephemeral=True)
    except Exception as e:
        print("Error with /add command", e)

@bot.tree.command(name="toggle_show_points", description="Show points (oooooo)")
@app_commands.checks.has_permissions(administrator=True)
async def toggle_show_points(interaction: discord.Interaction):
    try:
        bot.show_points = not bot.show_points
        await interaction.response.send_message(f"Point visibility: {bot.show_points}", ephemeral=True)
    except Exception as e:
        print("Error with /toggle_show_points command", e)

@bot.tree.command(name="list_users", description="List team members")
@app_commands.checks.has_permissions(administrator=True)
async def list_members(interaction: discord.Interaction):
    try:
        team, info  = await bot.teams_service.get_team_from_channel_id(interaction.channel_id, bot.database)
        if team is None:
            await interaction.response.send_message(f"No team information was found for you. Please contact <@726237123857874975>", ephemeral=True)
            return
        
        members = ""
        for i in range(len(team.members)):
            members += f"{bot.get_user(int(team.members[i])).display_name} ({bot.get_user(int(team.members[i]))})\n"
        
        await interaction.response.send_message(members, ephemeral=True)
        
    except Exception as e:
        print("Error with /list_users command", e)

# @bot.tree.command(name="rollback", description="Rollback 1")
# @app_commands.checks.has_permissions(administrator=True)
# async def rollback(interaction: discord.Interaction):
#     try:
#         team, info  = await bot.teams_service.get_team_from_channel_id(interaction.channel_id, bot.database)
#         if team is None:
#             await interaction.response.send_message(f"No team information was found for you. Please contact <@726237123857874975>", ephemeral=True)
#             return
        
#         rollback_tile = info["SubmissionHistory"][-1]
#         print(rollback_tile)
        
#         # Tile value
#         if rollback_tile[1] == 5:
#             bot.database.teams_collection.find_one_and_update(
#                         {"_id": ObjectId(team._id)},
#                         {"$set": {"Mini-sized": rollback_tile}},
#                         return_document = ReturnDocument.AFTER
#                     )
#         if rollback_tile[1] == 30:
#             bot.database.teams_collection.find_one_and_update(
#                         {"_id": ObjectId(team._id)},
#                         {"$set": {"Fun-sized": rollback_tile}},
#                         return_document = ReturnDocument.AFTER
#                     )
        
#         if rollback_tile[1] == 120:
#             bot.database.teams_collection.find_one_and_update(
#                         {"_id": ObjectId(team._id)},
#                         {"$set": {"Full-sized": rollback_tile}},
#                         return_document = ReturnDocument.AFTER
#                     )
        
#         if rollback_tile[1] == 250:
#             bot.database.teams_collection.find_one_and_update(
#                         {"_id": ObjectId(team._id)},
#                         {"$set": {"Family-sized": rollback_tile}},
#                         return_document = ReturnDocument.AFTER
#                     )
        
#     except Exception as e:
#         print("error with rollback: ", e)
    

@tasks.loop(minutes=5)
async def update_leaderboard():
    try:
        channel = bot.get_channel(int(bot.leaderboard_channel_id))
        leaderboard_message = await channel.fetch_message(int(bot.leaderboard_message_id))

        teams = await bot.teams_service.get_all_teams(bot.database)
        embed = await bot.embed_generator.make_topteams_embed(teams, bot.show_points)

        current_time = datetime.now() + timedelta(minutes=5)
        discord_timestamp = f"<t:{int(current_time.timestamp())}:R>"

        embed.description += f"\nNext update {discord_timestamp}"

        await leaderboard_message.edit(embed=embed)
    except Exception as e:
        print("Error with update_leaderboard timer", e)

@tasks.loop(minutes=5)
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
                        {"$set": {"Candy-bucket": None}}
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
                        updating=team.get("Updating", ""),
                        spreadsheet=team.get("Spreadsheet", ""),
                        image=team.get("Image", ""))
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
