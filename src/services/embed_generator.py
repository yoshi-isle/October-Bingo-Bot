import discord
from database import Team


class EmbedGenerator:
    async def make_team_embed(self, team: Team):
        try:
            desc = f"""Submit any of the following drops in https://discord.com/channels/1291519659585048677/1295840512452071505 to get candy!
                    \n**Mini-sized candy bar** (+5)\n{team.mini_task[0]["Name"]} - [wiki]({team.mini_task[0]["WikiUrl"]})
                    \n**Fun-sized candy bar** (+30)\n{team.fun_task[0]["Name"]} - [wiki]({team.fun_task[0]["WikiUrl"]})
                    \n**Full-sized candy bar** (+120)\n{team.full_task[0]["Name"]} - [wiki]({team.full_task[0]["WikiUrl"]})
                    \n**Family-sized candy bar** (+250)\n{team.family_task[0]["Name"]} - [wiki]({team.family_task[0]["WikiUrl"]})"""
            if team.bucket_task:
                desc += f"""\n\n**Candy bucket** (+600)\n{team.bucket_task[0]["Name"]} - [wiki]({team.bucket_task[0]["WikiUrl"]})"""
           
            embed = discord.Embed(title=f"{team.name}",
                        description= str(desc) ,
                        colour=0x700099)
            return embed
        except Exception as e:
            print(e)

       