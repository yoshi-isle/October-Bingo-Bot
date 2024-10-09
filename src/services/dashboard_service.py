import json
import discord
import random
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

class DashboardService:
    async def post_empty_dashboard(self, interaction: discord.Interaction):
        with Image.open("src/images/dashboard.png") as img:
            img.save("dashboard.png")
            final_image = discord.File("dashboard.png")
            await interaction.channel.send(file=final_image)

    async def generate_random_board(self, interaction: discord.Interaction):
        # Open the base dashboard image
        # Find the coordinates for mini, fun, full, family
        # For each tier, pick a random task

        slot1_coords = [700, 370]
        slot2_coords = [1115, 370]
        slot3_coords = [700, 740]
        slot4_coords = [1115, 740]

        random_mini_task = None
        random_fun_task = None
        random_full_task = None
        random_family_task = None

        # Get random tasks
        with open('src/tasks/mini_tasks.json', 'r') as file:
            data = json.load(file)
            random_mini_task = random.choice(data["tasks"])
        with open('src/tasks/fun_tasks.json', 'r') as file:
            data = json.load(file)
            random_fun_task = random.choice(data["tasks"])
        with open('src/tasks/full_tasks.json', 'r') as file:
            data = json.load(file)
            random_full_task = random.choice(data["tasks"])
        with open('src/tasks/family_tasks.json', 'r') as file:
            data = json.load(file)
            random_family_task = random.choice(data["tasks"])
        
        with Image.open("src/images/dashboard.png") as img:
            # Fetch the wiki image from the URL
            response_mini = requests.get(random_mini_task['Image'])
            response_fun = requests.get(random_fun_task['Image'])
            response_full = requests.get(random_full_task['Image'])
            response_family = requests.get(random_family_task['Image'])

            # Font
            draw = ImageDraw.Draw(img)
            text_color = (255, 255, 255)
            font = ImageFont.truetype("src/fonts/vinque rg.otf", 40)

            # Paste layer
            img_mini = Image.open(BytesIO(response_mini.content))
            img_mini.save("mini_image.png")
            position_mini = slot1_coords
            
            img_fun = Image.open(BytesIO(response_fun.content))
            img_fun.save("fun_image.png")
            position_fun = slot2_coords
            
            img_full = Image.open(BytesIO(response_full.content))
            img_full.save("full_image.png")
            position_full= slot3_coords

            img_family = Image.open(BytesIO(response_family.content))
            img_family.save("family_image.png")
            position_family = slot4_coords

            img.paste(img_mini, position_mini, img_mini)
            draw.text((600,500), random_mini_task['Name'], font=font, fill=text_color)
            img.paste(img_fun, position_fun, img_fun)
            img.paste(img_full, position_full, img_full)
            img.paste(img_family, position_family, img_family)

            img.save("final_dashboard.png")
            final_dashboard = discord.File("final_dashboard.png")

            await interaction.channel.send(file=final_dashboard)

        
        