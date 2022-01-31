import discord
from discord.ext import commands  # Again, we need this imported


class Meta(commands.Cog):
    """Collection of commands and events regarding the bot itself."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="ping")
    async def ping(self, ctx: commands.Context):
        """Get the bot's current websocket latency."""
        await ctx.send(
            f"Pong! {round(self.bot.latency * 1000)}ms"
        )  # It's now self.bot.latency

    @commands.command()
    async def prefix(self, ctx):
        """Return the bot's prefixes."""

        prefixes = await self.bot.get_prefix(ctx.message)
        # second form is for possible nicknames, but renders the same client-side
        del prefixes[1]
        embed = discord.Embed(
            title="Prefixes",
            colour=discord.Color.blurple(),
            description="\n".join(
                f"{index}. {elem}" for index, elem in enumerate(prefixes, 1)
            ),
        )
        embed.set_footer(text=f"{len(prefixes)} prefixes")
        await ctx.send(embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(Meta(bot))
