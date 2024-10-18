# from datetime import timedelta
import operator
import discord
from bson.objectid import ObjectId
from constants.candy_tier import CandyTier
from database import Database, Team
import database
from services.dashboard_service import DashboardService
from datetime import datetime, timedelta
from pymongo import ReturnDocument

class TeamService:
    async def get_all_teams(self, database: Database):
        # Sorted by points
        all_teams = [result for result in database.teams_collection.find()]
        # all_teams = (result for result in data)
        return sorted(all_teams, key=operator.itemgetter("Points"), reverse=True)
    
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
                bucket_task=team_data.get("Candy-bucket", ""),
                submission_history=team_data.get("SubmissionHistory", ""))
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
            print(f"An error occurred: {e}")
        
    async def reroll_task(self, team: Team, tier: CandyTier, database: Database, dashboard_service: DashboardService):
        try:
            if tier == CandyTier.CANDYTIER["Mini-sized"]:
                if team.mini_task[1] > datetime.now():
                    return "Your team cannot re-roll that slot yet."
            if tier == CandyTier.CANDYTIER["Fun-sized"]:
                if team.fun_task[1] > datetime.now():
                    return "Your team cannot re-roll that slot yet."
            if tier == CandyTier.CANDYTIER["Full-sized"]:
                if team.full_task[1] > datetime.now():
                    return "Your team cannot re-roll that slot yet."
            if tier == CandyTier.CANDYTIER["Family-sized"]:
                if team.family_task[1] > datetime.now():
                    return "Your team cannot re-roll that slot yet."
            return "Re-rolling!"
        
        except Exception as e:
            print(f"Error while re-rolling task: {e}")         
        


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
                bucket_task=updated_team.get("Candy-bucket", ""),
                submission_history=updated_team.get("SubmissionHistory", ""))

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
                bucket_task=team_data.get("Candy-bucket", ""),
                submission_history=team_data.get("SubmissionHistory", ""))
                
            return team, team_data
        else:
            return None, None
        
    async def award_points(self, team: Team, database, tier: CandyTier):
        try:
            if tier == CandyTier.CANDYTIER["Mini-sized"]:
                add_amount = 5
                new_submission_history = team.submission_history or []
                new_submission_history.append([team.mini_task[0]["Name"], add_amount])
                update_data = {"$set": {"Points": team.points + add_amount, "SubmissionHistory": new_submission_history}}

            elif tier == CandyTier.CANDYTIER["Fun-sized"]:
                add_amount = 30
                new_submission_history = team.submission_history or []
                new_submission_history.append([team.fun_task[0]["Name"], add_amount])
                update_data = {"$set": {"Points": team.points + add_amount, "SubmissionHistory": new_submission_history}}

            elif tier == CandyTier.CANDYTIER["Full-sized"]:
                add_amount = 120
                new_submission_history = team.submission_history or []
                new_submission_history.append([team.full_task[0]["Name"], add_amount])
                update_data = {"$set": {"Points": team.points + add_amount, "SubmissionHistory": new_submission_history}}

            elif tier == CandyTier.CANDYTIER["Family-sized"]:
                add_amount = 250
                new_submission_history = team.submission_history or []
                new_submission_history.append([team.family_task[0]["Name"], add_amount])
                update_data = {"$set": {"Points": team.points + add_amount, "SubmissionHistory": new_submission_history}}

            elif tier == CandyTier.CANDYTIER["Candy-bucket"]:
                add_amount = 600
                new_submission_history = team.submission_history or []
                new_submission_history.append([team.bucket_task[0]["Name"], add_amount])
                update_data = {"$set": {"Points": team.points + add_amount, "SubmissionHistory": new_submission_history}}

            print(update_data)
            return database.teams_collection.find_one_and_update(
                {"_id": ObjectId(team._id)},
                update_data,
                return_document=ReturnDocument.AFTER
            )
        except Exception as e:
            print(e)