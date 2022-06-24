import inspect
import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

from User_Commands.set_main_addr import set_main_addr





  

async def create_and_assign_gold_role(cl):
  curr_guild = cl.guilds[0]
  clt_member = curr_guild.get_member(cl.user.id)
  check = discord.utils.get(clt_member.roles, name=os.getenv("BOT_ROLE"))
  if check:
    return
  role = await curr_guild.create_role(name = os.getenv("BOT_ROLE"))
  await role.edit(color=discord.colour.Color.gold())
  await role.edit(position=1)
  await clt_member.add_roles(role)





    

class MainClient(commands.Bot):
    async def on_ready(self):
        print('Logged on as {0}!'.format(self.user))
        with open('discord-pic.png' , 'rb') as img:
          try:
            await client.user.edit(avatar=img.read())
          except discord.errors.HTTPException as e:
            None
        await create_and_assign_gold_role(client)
        # for command in commands:
        #   client.add_command(command)
        
        
          
          

  

load_dotenv()
client = MainClient(command_prefix=".")
client.add_command(set_main_addr)
client.run(os.getenv("BOT_PASSWORD"))

