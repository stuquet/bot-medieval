import discord
from discord.ext import commands
from private.config import token

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

bot.load_extension("basiccommands")

bot.run(token)
