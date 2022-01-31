import discord
from discord.ext import commands


class Welcome(commands.Cog):
    """Collection of commands and events regarding for welcoming new members."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener("on_guild_join")
    async def send_setup_request(self, guild: discord.Guild):
        """Send a message in the system channel to ask an Administrator to run the
        setup command.
        """
        pass

    @commands.Cog.listener("on_member_join")
    async def send_welcome_message(self, member: discord.Member):
        """Send the configurated welcome message to the system channel."""

        pass

    @commands.Cog.listener("on_member_join")
    async def add_default_role(self, member: discord.Member):
        """Add the configurated default role to the new member."""

        pass

    @commands.command()
    async def setup(self, ctx: commands.Context):
        """Setup the default role and welcome message sent to the system channel."""

        pass


def setup(bot):
    bot.add_cog(Welcome(bot))
