from datetime import datetime
import discord
from database import Team


class EmbedGenerator:
    async def make_team_embed(self, team: Team):
        try:
            # Reroll timestamps
            mini_task_disc_dt = f"<t:{round(team.mini_task[1].timestamp())}:R>"
            fun_task_disc_dt = f"<t:{round(team.fun_task[1].timestamp())}:R>"
            full_task_disc_dt = f"<t:{round(team.full_task[1].timestamp())}:R>"
            family_task_disc_dt = f"<t:{round(team.family_task[1].timestamp())}:R>"
            
            mini_reroll_text = f"Reroll: {mini_task_disc_dt}"
            fun_reroll_text = f"Reroll: {fun_task_disc_dt}"
            full_reroll_text = f"Reroll: {full_task_disc_dt}"
            family_reroll_text = f"Reroll: {family_task_disc_dt}"
            
            if team.mini_task[1] < datetime.now():
                mini_reroll_text = "*You can re-roll*"
            if team.fun_task[1] < datetime.now():
                fun_reroll_text = "*You can re-roll*"
            if team.full_task[1] < datetime.now():
                full_reroll_text = "*You can re-roll*"
            if team.family_task[1] < datetime.now():
                family_reroll_text = "*You can re-roll*"

    
            desc = f"""Submit any of the following drops in https://discord.com/channels/1291519659585048677/1295840512452071505 to get candy!
                    \n**Mini-sized candy bar** (+5)\n{team.mini_task[0]["Name"]} - [wiki]({team.mini_task[0]["WikiUrl"]})\n{mini_reroll_text}
                    \n**Fun-sized candy bar** (+30)\n{team.fun_task[0]["Name"]} - [wiki]({team.fun_task[0]["WikiUrl"]})\n{fun_reroll_text}
                    \n**Full-sized candy bar** (+120)\n{team.full_task[0]["Name"]} - [wiki]({team.full_task[0]["WikiUrl"]})\n{full_reroll_text}
                    \n**Family-sized candy bar** (+250)\n{team.family_task[0]["Name"]} - [wiki]({team.family_task[0]["WikiUrl"]})\n{family_reroll_text}"""
            if team.bucket_task:
                desc += f"""\n\n**Candy bucket** (+600)\n{team.bucket_task[0]["Name"]} - [wiki]({team.bucket_task[0]["WikiUrl"]})"""
           
            embed = discord.Embed(title=f"{team.name}",
                        description= str(desc) ,
                        colour=0x700099)
            return embed
        except Exception as e:
            print(e)

    async def make_topteams_embed(self, teams):
        try:
            placement = 1
            desc = ""
            for team in teams:
                if placement == 1:
                    desc += "🥇"
                elif placement == 2:
                    desc += "🥈"
                elif placement == 3:
                    desc += "🥉" 
                desc += f"{team['Name']}\n"
                placement += 1
            
            embed = discord.Embed(title=f"🏆 **Current Top Teams** 🏆",
            description= str(desc) ,
            colour=0xfcf403)
            return embed
        except Exception as e:
            print(e)