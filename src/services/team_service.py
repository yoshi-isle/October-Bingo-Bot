# from datetime import timedelta
import discord
from bson.objectid import ObjectId
from constants.candy_tier import CandyTier
from database import Database, Team
import database
from services.dashboard_service import DashboardService
from datetime import datetime, timedelta
from pymongo import ReturnDocument

class TeamService:
    async def get_all_teams(self, interaction: discord.Interaction, database: Database):
        await interaction.response.send_message(await database.get_all_teams())
    
    async def get_team_from_channel_id(self, channel_id: str, database: Database) -> Team:
        team_data = database.teams_collection.find_one({"ChannelId": str(channel_id)})

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
                family_task=team_data.get("Family-sized", ""),
                bucket_task=team_data.get("Candy-bucket", ""))
            return team
        else:
            return None
    
    async def initialize_team(self, channel_name: str, channel_id: str, database: Database, dashboard_service: DashboardService):
        try:
            channel_id = str(channel_id)
            # If it already exists, throw
            exists = await self.get_team_from_channel_id(channel_id, database)

            if exists:
                print("Team already exists.")
                return
            # Inserting a new document into the 'teams_collection'
            database.teams_collection.insert_one({
                "Name": channel_name,
                "Members": [],
                "Points": 0,
                "ChannelId": channel_id,
                "Mini-sized": None,
                "Fun-sized": None,
                "Full-sized": None,
                "Family-sized": None,
                "Candy-bucket": None,
                "SubmissionHistory": []
            })

            created_team = await self.get_team_from_channel_id(channel_id, database)

            await self.assign_task(created_team, CandyTier.CANDYTIER["Mini-sized"], database, dashboard_service)
            await self.assign_task(created_team, CandyTier.CANDYTIER["Fun-sized"], database, dashboard_service)
            await self.assign_task(created_team, CandyTier.CANDYTIER["Full-sized"], database, dashboard_service)
            await self.assign_task(created_team, CandyTier.CANDYTIER["Family-sized"], database, dashboard_service)

            created_team = await self.get_team_from_channel_id(channel_id, database)

            return created_team

        except Exception as e:
            # Handle exceptions as needed
            print(f"An error occurred: {e}")

    async def assign_task(self, team: Team, tier: CandyTier, database: Database, dashboard_service: DashboardService):
        twelve_hours_from_now = datetime.now() + timedelta(hours=12)
        random_task = await dashboard_service.get_random_task(tier)
        try:
            
            update_data = {"$set": {tier.name: [random_task, twelve_hours_from_now]}}

            updated_team = database.teams_collection.find_one_and_update(
                {"_id": ObjectId(team._id)},
                update_data,
                return_document=ReturnDocument.AFTER
            )

            team = Team(
                _id=updated_team.get("_id", ""),
                name=updated_team.get("Name", ""),
                members=updated_team.get("Members", []),
                points=updated_team.get("Points", 0),
                channel_id=updated_team.get("ChannelId", ""),
                mini_task=updated_team.get("Mini-sized", ""),
                fun_task=updated_team.get("Fun-sized", ""),
                full_task=updated_team.get("Full-sized", ""),
                family_task=updated_team.get("Family-sized", ""),
                bucket_task=updated_team.get("Candy-bucket", ""))

            return team
        except Exception as e:
            print(f"Failed to update database record {e}")
    
    async def get_team_from_user_id(self, user_id: str, database):
        team_data = database.teams_collection.find_one({"Members": user_id})
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
                family_task=team_data.get("Family-sized", ""),
                bucket_task=team_data.get("Candy-bucket", ""))
            return team, team_data
        else:
            return None, None
        
    async def award_points(self, team: Team, database, tier: CandyTier):
        try:
            add_amount = 0
            if tier == CandyTier.CANDYTIER["Mini-sized"]:
                add_amount = 5
            elif tier == CandyTier.CANDYTIER["Fun-sized"]:
                add_amount = 30
            elif tier == CandyTier.CANDYTIER["Full-sized"]:
                add_amount = 120
            elif tier == CandyTier.CANDYTIER["Family-sized"]:
                add_amount = 250
            
            update_data = {"$set": {"Points": team.points + add_amount}}

            return database.teams_collection.find_one_and_update(
                {"_id": ObjectId(team._id)},
                update_data,
                return_document=ReturnDocument.AFTER
            )
        except Exception as e:
            print(e)