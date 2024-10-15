import json
import random
import aiohttp
import asyncio
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import discord
from enum import Enum
from constants.candy_tier import CandyTier
from database import Team

class TaskLoader:
    def __init__(self):
        self.mini_tasks = self.load_tasks('src/tasks/mini_tasks.json')
        self.fun_tasks = self.load_tasks('src/tasks/fun_tasks.json')
        self.full_tasks = self.load_tasks('src/tasks/full_tasks.json')
        self.family_tasks = self.load_tasks('src/tasks/family_tasks.json')

    @staticmethod
    def load_tasks(file_path):
        with open(file_path, 'r') as file:
            return json.load(file)["tasks"]

class DashboardService:
    def __init__(self):
        # Cache tasks
        self.task_loader = TaskLoader()
        self.slot1_coords = [688, 344]
        self.slot2_coords = [1102, 344]
        self.slot3_coords = [682, 711]
        self.slot4_coords = [1102, 711]
        self.text1_coords = [600, 516]
        self.text2_coords = [1025, 516]
        self.text3_coords = [600, 888]
        self.text4_coords = [1025, 888]

    """
    Generate the team's bingo board image
    """
    async def generate_board(self, team: Team):
        # Helper
        async def fetch_image(session, url):
            async with session.get(url) as response:
                return await response.read()
            
        async with aiohttp.ClientSession() as session:
            response_mini, response_fun, response_full, response_family = await asyncio.gather(
                fetch_image(session, team.tasks.get('MiniTask')['Image']),
                fetch_image(session, team.tasks.get('FunTask')['Image']),
                fetch_image(session, team.tasks.get('FullTask')['Image']),
                fetch_image(session, team.tasks.get('FamilyTask')['Image']),
            )

        with Image.open("src/images/dashboard.png") as img:
            # Font and draw setup
            draw = ImageDraw.Draw(img)
            font = ImageFont.truetype("src/fonts/vinque rg.otf", 28)
            text_color = (255, 255, 255)

            # Open images from memory and paste them
            img_mini = Image.open(BytesIO(response_mini))
            img_fun = Image.open(BytesIO(response_fun))
            img_full = Image.open(BytesIO(response_full))
            img_family = Image.open(BytesIO(response_family))

            img.paste(img_mini, self.slot1_coords, img_mini)
            img.paste(img_fun, self.slot2_coords, img_fun)
            img.paste(img_full, self.slot3_coords, img_full)
            img.paste(img_family, self.slot4_coords, img_family)
            draw.text(self.text1_coords, random_mini_task['Name'], font=font, fill=text_color)
            draw.text(self.text2_coords, random_fun_task['Name'], font=font, fill=text_color)
            draw.text(self.text3_coords, random_full_task['Name'], font=font, fill=text_color)
            draw.text(self.text4_coords, random_family_task['Name'], font=font, fill=text_color)

            img.save("final_dashboard.png")
            final_dashboard = discord.File("final_dashboard.png")

            return final_dashboard
        
    async def get_random_task(self, tier: CandyTier):
        if tier == CandyTier.CANDYTIER["Mini-sized"]:
            return random.choice(self.task_loader.mini_tasks)
        if tier == CandyTier.CANDYTIER["Fun-sized"]:
            return random.choice(self.task_loader.fun_tasks)
        if tier == CandyTier.CANDYTIER["Full-sized"]:
            return random.choice(self.task_loader.full_tasks)
        if tier == CandyTier.CANDYTIER["Family-sized"]:
            return random.choice(self.task_loader.family_tasks)