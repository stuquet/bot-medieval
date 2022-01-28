from discord.ext import commands


class Plague(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot



def setup(bot: commands.Bot):
    bot.add_cog(Plague(bot))
