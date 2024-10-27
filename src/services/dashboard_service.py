import json
import random
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import discord
import requests
from constants.candy_tier import CandyTier
from database import Team
import gc

class TaskLoader:
    def __init__(self):
        self.load_tasks()

    def load_tasks(self):
        # Reload tasks when this method is called
        self.mini_tasks = self._load_tasks_from_file('src/tasks/mini_tasks.json')
        self.fun_tasks = self._load_tasks_from_file('src/tasks/fun_tasks.json')
        self.full_tasks = self._load_tasks_from_file('src/tasks/full_tasks.json')
        self.family_tasks = self._load_tasks_from_file('src/tasks/family_tasks.json')
        self.candy_bucket_tasks = self._load_tasks_from_file('src/tasks/bucket_tasks.json')

    @staticmethod
    def _load_tasks_from_file(file_path):
        with open(file_path, 'r') as file:
            return json.load(file)["tasks"]

class DashboardService:
    def __init__(self):
        self.task_loader = TaskLoader()

        self.slot1_box = [633, 289, 888, 544]
        self.slot2_box = [1047, 289, 1302, 544]
        self.slot3_box = [627, 656, 882, 911]
        self.slot4_box = [1047, 656, 1302, 911]
        self.bucket_box = [1478, 503, 1738, 758]

        self.taskname1_coords = [600, 530]
        self.taskname2_coords = [1025, 530]
        self.taskname3_coords = [600, 900]
        self.taskname4_coords = [1025, 900]
        self.bucketname_coords = [1450, 745]

        self.pointamount1_coords = [855, 260]
        self.pointamount2_coords = [1255, 260]
        self.pointamount3_coords = [820, 640]
        self.pointamount4_coords = [1230, 640]
        self.bucketamount_coords = [1670, 480]

        self.tasktier1_coords = [600, 270]
        self.tasktier2_coords = [1025, 270]
        self.tasktier3_coords = [600, 645]
        self.tasktier4_coords = [1018, 645]
        self.buckettasktier_coords = [1456, 480]
        
        # Bucket panel coordinates
        self.bucketpanel = [1430, 460]

        self.max_image_size = (200, 200)

    async def generate_board(self, team: Team):
        try:
            response_mini = Image.open(team.mini_task[0]['Image']).convert("RGBA")
            response_fun = Image.open(team.fun_task[0]['Image']).convert("RGBA")
            response_full = Image.open(team.full_task[0]['Image']).convert("RGBA")
            response_family = Image.open(team.family_task[0]['Image']).convert("RGBA")
            
            if team.bucket_task:
                response_bucket = Image.open(team.bucket_task[0]['Image']).convert("RGBA")
                star_panel = Image.open("src/images/star.png").convert("RGBA")
                
            with Image.open("src/images/dashboard.png") as img:
                tier_image_mini = Image.open("src/images/mini_candy.png").convert("RGBA")
                tier_image_fun = Image.open("src/images/fun_candy.png").convert("RGBA")
                tier_image_full = Image.open("src/images/full_candy.png").convert("RGBA")
                tier_image_family = Image.open("src/images/family_candy.png").convert("RGBA")
                tier_image_bucket = Image.open("src/images/candy_bucket.png").convert("RGBA")
                
                img.paste(tier_image_mini, [830, 485], tier_image_mini)
                img.paste(tier_image_fun, [1250, 485], tier_image_fun)
                img.paste(tier_image_full, [825, 865], tier_image_full)
                img.paste(tier_image_family, [1253, 885], tier_image_family)
                
                # Font and draw setup
                draw = ImageDraw.Draw(img)
                
                small_font = ImageFont.truetype("src/fonts/vinque rg.otf", 26)
                big_font = ImageFont.truetype("src/fonts/vinque rg.otf", 40)
                
                text_color_white = (255, 255, 255)
                text_color_orange = (255, 165, 0)
                text_color_green = (0, 255, 0)
                text_color_yellow = (255, 255, 0)

                # Convert fetched images into RGBA format to ensure transparency is preserved
                img_mini = Image.open(BytesIO(response_mini.content)).convert("RGBA")
                img_fun = Image.open(BytesIO(response_fun.content)).convert("RGBA")
                img_full = Image.open(BytesIO(response_full.content)).convert("RGBA")
                img_family = Image.open(BytesIO(response_family.content)).convert("RGBA")
                if team.bucket_task:
                    img_bucket = Image.open(BytesIO(response_bucket.content)).convert("RGBA")

                # Resize images while maintaining aspect ratio
                img_mini = self._resize_image(img_mini)
                img_fun = self._resize_image(img_fun)
                img_full = self._resize_image(img_full)
                img_family = self._resize_image(img_family)
                if team.bucket_task:
                    img_bucket = self._resize_image(img_bucket)

                # Calculate the center coordinates for each image based on the region box
                mini_coords = self._get_center_coords(self.slot1_box, img_mini.size)
                fun_coords = self._get_center_coords(self.slot2_box, img_fun.size)
                full_coords = self._get_center_coords(self.slot3_box, img_full.size)
                family_coords = self._get_center_coords(self.slot4_box, img_family.size)
                if team.bucket_task:
                    bucket_coords = self._get_center_coords(self.bucket_box, img_bucket.size)

                # Paste images onto the base image at the calculated coordinates
                img.paste(img_mini, mini_coords, img_mini)
                img.paste(img_fun, fun_coords, img_fun)
                img.paste(img_full, full_coords, img_full)
                img.paste(img_family, family_coords, img_family)
                if team.bucket_task:
                    img.paste(star_panel, self.bucketpanel, star_panel)
                    img.paste(img_bucket,  bucket_coords, img_bucket)
                    img.paste(tier_image_bucket, [1690, 705], tier_image_bucket)

                # Add task names as text
                draw.text(self.taskname1_coords, team.mini_task[0]['Name'], font=small_font, fill=text_color_white)
                draw.text(self.taskname2_coords, team.fun_task[0]['Name'], font=small_font, fill=text_color_white)
                draw.text(self.taskname3_coords, team.full_task[0]['Name'], font=small_font, fill=text_color_white)
                draw.text(self.taskname4_coords, team.family_task[0]['Name'], font=small_font, fill=text_color_white)
                if team.bucket_task:
                    draw.text(self.bucketname_coords, team.bucket_task[0]['Name'], font=small_font, fill=text_color_white)
                    
                # Add task point amounts as text
                draw.text(self.pointamount1_coords, "+5", font=big_font, fill=text_color_green)
                draw.text(self.pointamount2_coords, "+30", font=big_font, fill=text_color_green)
                draw.text(self.pointamount3_coords, "+120", font=big_font, fill=text_color_green)
                draw.text(self.pointamount4_coords, "+250", font=big_font, fill=text_color_green)
                if team.bucket_task:
                    draw.text(self.bucketamount_coords, "+600", font=big_font, fill=text_color_yellow)
                    
                # Add task tier names as text
                draw.text(self.tasktier1_coords, "Mini-sized", font=small_font, fill=text_color_orange)
                draw.text(self.tasktier2_coords, "Fun-sized", font=small_font, fill=text_color_orange)
                draw.text(self.tasktier3_coords, "Full-sized", font=small_font, fill=text_color_orange)
                draw.text(self.tasktier4_coords, "Family-sized", font=small_font, fill=text_color_orange)
                if team.bucket_task:
                    draw.text(self.buckettasktier_coords, "Candy bucket", font=small_font, fill=text_color_orange)
                    
                # Save final image
                img.save("final_dashboard.png")
                final_dashboard = discord.File("final_dashboard.png")
                gc.collect()
                return final_dashboard

        except Exception as e:
            print(f"Error generating dashboard: {e}")

    """Resize the image while maintaining aspect ratio."""
    @staticmethod
    def _resize_image(image):
        image.thumbnail((200, 200))
        return image

    """Calculate the top-left corner coordinates to center the image in the given region box."""
    @staticmethod
    def _get_center_coords(region_box, image_size):
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
        if tier == CandyTier.CANDYTIER["Candy-bucket"]:
                return random.choice(self.task_loader.candy_bucket_tasks)
