import discord
from discord.ext import commands
from private.config import token


# see https://youtu.be/g_wlZ9IhbTs
def main():
    intents = discord.Intents.default()
    intents.members = True

    bot = commands.Bot(command_prefix="!", intents=intents)

    cogs = ["cogs.info", "cogs.plague"]
    for cog in cogs:
        bot.load_extension(cog)

    bot.run(token)


if __name__ == "__main__":
    main()
