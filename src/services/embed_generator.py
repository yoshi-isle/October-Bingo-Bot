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
            if team.bucket_task:
                bucket_task_disc_dt = f"<t:{round(team.bucket_task[1].timestamp())}:R>"
            
            mini_reroll_text = f"🎲 Reroll: {mini_task_disc_dt}"
            fun_reroll_text = f"🎲 Reroll: {fun_task_disc_dt}"
            full_reroll_text = f"🎲 Reroll: {full_task_disc_dt}"
            family_reroll_text = f"🎲 Reroll: {family_task_disc_dt}"
            if team.bucket_task:
                bucket_expire_text = f"⚠️ Expires: {bucket_task_disc_dt}"
            
            
            if team.mini_task[1] < datetime.now():
                mini_reroll_text = "🎲 *You can re-roll*"
            if team.fun_task[1] < datetime.now():
                fun_reroll_text = "🎲 *You can re-roll*"
            if team.full_task[1] < datetime.now():
                full_reroll_text = "🎲 *You can re-roll*"
            if team.family_task[1] < datetime.now():
                family_reroll_text = "🎲 *You can re-roll*"
            
            partial_counter_text_mini = "Requires **1** submission"
            partial_counter_text_fun = "Requires **1** submission"
            partial_counter_text_full = "Requires **1** submission"
            partial_counter_text_family = "Requires **1** submission"
            partial_counter_text_bucket = "Requires **1** submission"
            
            if int(team.mini_task[0]['CompletionCounter']) > 1:
                partial_counter_text_mini = f"Requires **{team.mini_task[0]['CompletionCounter']}** more submissions"
            if int(team.fun_task[0]['CompletionCounter']) > 1:
                partial_counter_text_fun = f"Requires **{team.fun_task[0]['CompletionCounter']}** more submissions"
            if int(team.full_task[0]['CompletionCounter']) > 1:
                partial_counter_text_full = f"Requires **{team.full_task[0]['CompletionCounter']}** more submissions"
            if int(team.family_task[0]['CompletionCounter']) > 1:
                partial_counter_text_family = f"Requires **{team.family_task[0]['CompletionCounter']}** more submissions"
            if team.bucket_task:
                if int(team.bucket_task[0]['CompletionCounter']) > 1:
                    partial_counter_text_bucket = f"Requires **{team.bucket_task[0]['CompletionCounter']}** submissions"
    
            desc = f"""Submit any of the following drops in https://discord.com/channels/1290136938115891220/1295850896009330698 to get candy!
                    \n**Mini-sized candy bar** (+5)\n> {team.mini_task[0]["Description"]} - [wiki]({team.mini_task[0]["WikiUrl"]})\n> {partial_counter_text_mini}\n> {mini_reroll_text}
                    \n**Fun-sized candy bar** (+30)\n> {team.fun_task[0]["Description"]} - [wiki]({team.fun_task[0]["WikiUrl"]})\n> {partial_counter_text_fun}\n> {fun_reroll_text}
                    \n**Full-sized candy bar** (+120)\n> {team.full_task[0]["Description"]} - [wiki]({team.full_task[0]["WikiUrl"]})\n> {partial_counter_text_full}\n> {full_reroll_text}
                    \n**Family-sized candy bar** (+250)\n> {team.family_task[0]["Description"]} - [wiki]({team.family_task[0]["WikiUrl"]})\n> {partial_counter_text_family}\n> {family_reroll_text}"""
            if team.bucket_task:
                desc += f"""\n\n**Candy bucket** (+600)\n> {team.bucket_task[0]["Name"]} - [wiki]({team.bucket_task[0]["WikiUrl"]})\n> {partial_counter_text_bucket}\n> {bucket_expire_text}"""
           
            embed = discord.Embed(title=f"{team.name}",
                        description= str(desc) ,
                        colour=0x700099)
            return embed
        except Exception as e:
            print(e)

    async def make_topteams_embed(self, teams):
        try:
            teams.sort(key=lambda x: x['Points'], reverse=True)
            
            placement = 1
            last_score = None
            desc = ""

            for index, team in enumerate(teams):
                # Check if the current team has the same score as the last one
                if last_score is not None and team['Points'] != last_score:
                    placement += 1

                last_score = team['Points']
                if placement == 1:
                    desc += "🥇"
                elif placement == 2:
                    desc += "🥈"
                elif placement == 3:
                    desc += "🥉"

                desc += f"**{team['Name']}**\n"

            embed = discord.Embed(
                title="🏆 **Current Top Teams** 🏆",
                description=desc,
                colour=0xfcf403
            )
            return embed
        except Exception as e:
            print(e)

