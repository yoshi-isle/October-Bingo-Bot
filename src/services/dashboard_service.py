import json
import discord
import random
import requests
from PIL import Image
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

        slot1_coords = (695, 370)

        random_task = None

        with open('src/tasks/mini_tasks.json', 'r') as file:
            data = json.load(file)
            random_task = random.choice(data["tasks"])
            print(random_task)

        with Image.open("src/images/dashboard.png") as img:

            # Fetch the wiki image from the URL
            response = requests.get(random_task['Image'])
            print(response.content)
            print(random_task)
            # Open the image from the URL using BytesIO
            mini = Image.open(BytesIO(response.content))
            mini.save("mini_image.png")
            final_image = discord.File("mini_image.png")

            await interaction.channel.send(file=final_image)