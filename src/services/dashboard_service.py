import json
import random
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import discord
import requests
from constants.candy_tier import CandyTier
from database import Team

class TaskLoader:
    def __init__(self):
        self.load_tasks()

    def load_tasks(self):
        # Reload tasks when this method is called
        self.mini_tasks = self._load_tasks_from_file('src/tasks/mini_tasks.json')
        self.fun_tasks = self._load_tasks_from_file('src/tasks/fun_tasks.json')
        self.full_tasks = self._load_tasks_from_file('src/tasks/full_tasks.json')
        self.family_tasks = self._load_tasks_from_file('src/tasks/family_tasks.json')

    @staticmethod
    def _load_tasks_from_file(file_path):
        with open(file_path, 'r') as file:
            return json.load(file)["tasks"]

class DashboardService:
    def __init__(self):
        self.task_loader = TaskLoader()  # Initialize task loader
        self.slot1_coords = [688, 344]
        self.slot2_coords = [1102, 344]
        self.slot3_coords = [682, 711]
        self.slot4_coords = [1102, 711]
        self.text1_coords = [600, 516]
        self.text2_coords = [1025, 516]
        self.text3_coords = [600, 888]
        self.text4_coords = [1025, 888]
        self.image_size = (300, 300)

    """
    Generate the team's bingo board image
    """
    async def generate_board(self, team: Team):
        try:
            response_mini = requests.get(team.mini_task[0]['Image'])
            response_fun = requests.get(team.fun_task[0]['Image'])
            response_full = requests.get(team.full_task[0]['Image'])
            response_family = requests.get(team.family_task[0]['Image'])

            # Open base dashboard image
            with Image.open("src/images/dashboard.png") as img:
                # Font and draw setup
                draw = ImageDraw.Draw(img)
                font = ImageFont.truetype("src/fonts/vinque rg.otf", 28)
                text_color = (255, 255, 255)

                # Convert fetched images into RGBA format to ensure transparency is preserved
                img_mini = Image.open(BytesIO(response_mini.content))
                img_fun = Image.open(BytesIO(response_fun.content))
                img_full = Image.open(BytesIO(response_full.content))
                img_family = Image.open(BytesIO(response_family.content))

                img_mini = img_mini.resize(self.image_size)
                img_fun = img_fun.resize(self.image_size)
                img_full = img_full.resize(self.image_size)
                img_family = img_family.resize(self.image_size)

                img_mini = img_mini.convert("RGBA")
                img_fun = img_fun.convert("RGBA")
                img_full = img_full.convert("RGBA")
                img_family = img_family.convert("RGBA")

                print("4")
                # Paste images onto the base image at the designated coordinates
                img.paste(img_mini, self.slot1_coords, img_mini)
                img.paste(img_fun, self.slot2_coords, img_fun)
                img.paste(img_full, self.slot3_coords, img_full)
                img.paste(img_family, self.slot4_coords, img_family)

                print("5")
                # Add task names as text
                draw.text(self.text1_coords, team.mini_task[0]['Name'], font=font, fill=text_color)
                draw.text(self.text2_coords, team.fun_task[0]['Name'], font=font, fill=text_color)
                draw.text(self.text3_coords, team.full_task[0]['Name'], font=font, fill=text_color)
                draw.text(self.text4_coords, team.family_task[0]['Name'], font=font, fill=text_color)

                print("6")
                # Save final image and return the file object to be sent to Discord
                img.save("final_dashboard.png")
                final_dashboard = discord.File("final_dashboard.png")
                return final_dashboard

        except Exception as e:
            print(f"Error generating dashboard: {e}")

    async def get_random_task(self, tier: CandyTier):
        if tier == CandyTier.CANDYTIER["Mini-sized"]:
            return random.choice(self.task_loader.mini_tasks)
        if tier == CandyTier.CANDYTIER["Fun-sized"]:
            return random.choice(self.task_loader.fun_tasks)
        if tier == CandyTier.CANDYTIER["Full-sized"]:
            return random.choice(self.task_loader.full_tasks)
        if tier == CandyTier.CANDYTIER["Family-sized"]:
            return random.choice(self.task_loader.family_tasks)