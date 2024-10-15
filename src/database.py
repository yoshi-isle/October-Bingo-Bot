import json

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

from constants.cluster_names import MongodbConstants

class Database:
    def __init__(self):
        with open('appSettings.local.json', 'r') as file:
            data = json.load(file)

        self.mongo_uri = data["mongo"]["connection_string"]
        self._connect()

    def _connect(self):
        self.client = MongoClient(self.mongo_uri, server_api=ServerApi("1"))
        try:
            self.client.admin.command("ping")
        except Exception as e:
            print(f"mongo did not connect: {e}")

        self.db = self.client[MongodbConstants.cluster_name]
        self.teams_collection = self.db[MongodbConstants.collection_teams]

    def _disconnect(self):
        self.client.close()
        
    async def get_team_info(self, channel_id):
        return self.teams_collection.find_one({"ChannelId": str(channel_id)})

    async def get_all_teams(self):
        return [result for result in self.teams_collection.find()]

class Team:
    def __init__(self, _id, name, members, points, channel_id, mini_task, fun_task, full_task, family_task):
        self._id = _id
        self.name = name
        self.members = members
        self.points = points
        self.channel_id = channel_id
        self.mini_task = mini_task
        self.fun_task = fun_task
        self.full_task = full_task
        self.family_task = family_task