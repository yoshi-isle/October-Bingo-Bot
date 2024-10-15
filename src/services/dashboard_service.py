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
        self.task_loader = TaskLoader()
        self.slot1_box = [633, 289, 888, 544]   # Shifted right 25px and down 25px
        self.slot2_box = [1047, 289, 1302, 544]  # Shifted
        self.slot3_box = [627, 656, 882, 911]    # Shifted
        self.slot4_box = [1047, 656, 1302, 911]  # Shifted


        self.text1_coords = [600, 516]
        self.text2_coords = [1025, 516]
        self.text3_coords = [600, 888]
        self.text4_coords = [1025, 888]
        self.max_image_size = (200, 200)

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

                # Resize images while maintaining aspect ratio
                img_mini = self._resize_image(img_mini)
                img_fun = self._resize_image(img_fun)
                img_full = self._resize_image(img_full)
                img_family = self._resize_image(img_family)

                # Calculate the center coordinates for each image based on the region box
                mini_coords = self._get_center_coords(self.slot1_box, img_mini.size)
                fun_coords = self._get_center_coords(self.slot2_box, img_fun.size)
                full_coords = self._get_center_coords(self.slot3_box, img_full.size)
                family_coords = self._get_center_coords(self.slot4_box, img_family.size)

                # Paste images onto the base image at the calculated coordinates
                img.paste(img_mini, mini_coords, img_mini)
                img.paste(img_fun, fun_coords, img_fun)
                img.paste(img_full, full_coords, img_full)
                img.paste(img_family, family_coords, img_family)

                # Add task names as text
                draw.text(self.text1_coords, team.mini_task[0]['Name'], font=font, fill=text_color)
                draw.text(self.text2_coords, team.fun_task[0]['Name'], font=font, fill=text_color)
                draw.text(self.text3_coords, team.full_task[0]['Name'], font=font, fill=text_color)
                draw.text(self.text4_coords, team.family_task[0]['Name'], font=font, fill=text_color)

                # Save final image and return the file object to be sent to Discord
                img.save("final_dashboard.png")
                final_dashboard = discord.File("final_dashboard.png")
                return final_dashboard

        except Exception as e:
            print(f"Error generating dashboard: {e}")

    @staticmethod
    def _resize_image(image):
        """Resize the image while maintaining aspect ratio."""
        image.thumbnail((200, 200))  # Resize while keeping aspect ratio
        return image

    @staticmethod
    def _get_center_coords(region_box, image_size):
        """Calculate the top-left corner coordinates to center the image in the given region box."""
        region_width = region_box[2] - region_box[0]
        region_height = region_box[3] - region_box[1]
        
        image_width, image_height = image_size
        
        # Calculate the top-left corner for centering
        left = region_box[0] + (region_width - image_width) // 2
        top = region_box[1] + (region_height - image_height) // 2
        
        return (left, top)

    async def get_random_task(self, tier: CandyTier):
        if tier == CandyTier.CANDYTIER["Mini-sized"]:
            return random.choice(self.task_loader.mini_tasks)
        if tier == CandyTier.CANDYTIER["Fun-sized"]:
            return random.choice(self.task_loader.fun_tasks)
        if tier == CandyTier.CANDYTIER["Full-sized"]:
            return random.choice(self.task_loader.full_tasks)
        if tier == CandyTier.CANDYTIER["Family-sized"]:
            return random.choice(self.task_loader.family_tasks)