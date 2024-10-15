# from datetime import timedelta
import discord
from bson.objectid import ObjectId
from constants.candy_tier import CandyTier
from database import Database, Team
import database
from services.dashboard_service import DashboardService
from datetime import datetime, timedelta

class TeamService:
    async def get_all_teams(self, interaction: discord.Interaction, database: Database):
        await interaction.response.send_message(await database.get_all_teams())
    
    async def get_team_from_channel_id(self, interaction: discord.Interaction, database: Database) -> Team:
        team_data = database.teams_collection.find_one({"ChannelId": str(interaction.channel_id)})

        if team_data:
            team = Team(
                _id=team_data.get("_id", ""),
                name=team_data.get("Name", ""),
                members=team_data.get("Members", []),
                points=team_data.get("Points", 0),
                channel_id=team_data.get("ChannelId", ""),
                mini_task=team_data.get("Mini-sized", ""),
                fun_task=team_data.get("Fun-sized", ""),
                full_task=team_data.get("Full-sized", ""),
                family_task=team_data.get("Family-sized", ""))
            return team
        else:
            return None

    async def assign_task(self, team: Team, tier: CandyTier, database: Database, dashboard_service: DashboardService):
        twelve_hours_from_now = datetime.now() + timedelta(hours=12)
        random_task = await dashboard_service.get_random_task(tier)
        try:
            update_data = {"$set": {tier.name: [random_task, twelve_hours_from_now]}}
            updated = database.teams_collection.update_one({"_id": ObjectId(team._id)}, update_data)
            return updated
        except Exception as e:
            print(f"Failed to update database record {e}")
       