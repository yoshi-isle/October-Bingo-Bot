# from datetime import timedelta
import discord
from bson.objectid import ObjectId
from constants.candytier import CandyTier
from database import Database, Team
from services.dashboard_service import DashboardService
from datetime import datetime, timedelta

class TeamService:
    async def get_all_teams(self, interaction: discord.Interaction, database: Database):
        await interaction.response.send_message(await database.get_all_teams())
    
    async def get_team_from_channel_id(self, interaction: discord.Interaction, database: Database):
        return database.teams_collection.find_one({"ChannelId": str(interaction.channel_id)})
    
    async def assign_task(self, team: Team, tier: CandyTier):
        twelve_hours_from_now = datetime.now() + timedelta(hours=12)
        update_data = {"$set": {tier.value: [DashboardService.get_random_task(tier=tier), twelve_hours_from_now]}}
        return self.pb_collection.update_one({"_id": ObjectId(team.id)}, update_data)