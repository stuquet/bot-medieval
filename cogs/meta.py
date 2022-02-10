import discord
from discord.ext import commands  # Again, we need this imported


class Prefix(commands.Converter):
    async def convert(self, ctx, argument):
        user_id = ctx.bot.user.id
        if argument.startswith((f"<@{user_id}>", f"<@!{user_id}>")):
            raise commands.BadArgument("That is a reserved prefix already in use.")
        return argument


class Meta(commands.Cog):
    """Collection of commands and events regarding the bot itself."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

        self.bot.loop.run_until_complete(self._create_tables())

    @commands.command(name="ping")
    async def ping(self, ctx: commands.Context):
        """Get the bot's current websocket latency."""
        await ctx.send(
            f"Pong! {round(self.bot.latency * 1000)}ms"
        )  # It's now self.bot.latency

    @commands.group(invoke_without_command=True)
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

    @prefix.command(name="add", aliases=["set"], ignore_extra=False)
    @commands.has_guild_permissions(manage_guild=True)
    async def prefix_add(self, ctx, prefix: Prefix):
        """Add a prefix to which the bot will respond in the guild.

        You must have the Manage Server permission to use this command.
        """

        await self._add_prefix(ctx.guild, prefix)

    @prefix.command(name="remove", aliases=["delete", "del"], ignore_extra=False)
    @commands.has_guild_permissions(manage_guild=True)
    async def prefix_remove(self, ctx, prefix: Prefix):
        """Remove a prefix from the list of custom prefix.

        You must have the Manage Server permission to use this command.
        """

        await self._remove_prefix(ctx.guild, prefix)

    @prefix_add.error
    @prefix_remove.error
    async def prefix_add_remove_error(self, ctx, error):
        """Error handler for the prefix add and remove subcommands."""

        if isinstance(error, commands.TooManyArguments):
            await ctx.reply(
                "You've given too many prefixes. "
                "Either quote it or only do it one by one."
            )

        elif isinstance(error, commands.BadArgument):
            await ctx.reply(error)

        else:
            raise error

    @prefix_add.after_invoke
    @prefix_remove.after_invoke
    async def prefix_add_remove_after(self, ctx):
        """Add a reaction according to the success of the command."""

        if not ctx.command_failed:
            await ctx.message.add_reaction("\N{WHITE HEAVY CHECK MARK}")

        else:
            await ctx.message.add_reaction("\N{CROSS MARK}")

    async def get_guild_prefixes(self, guild):
        prefixes = await self._get_guild_prefixes(guild)
        return [p["prefix"] for p in prefixes]

    async def _create_tables(self):
        """Create the necessary DB tables if they do not exist."""

        await self.bot.db.execute(
            """
            CREATE TABLE IF NOT EXISTS meta_prefix(
                guild_id INTEGER NOT NULL,
                prefix   TEXT    NOT NULL
            )
            """
        )

        await self.bot.db.commit()

    async def _add_prefix(self, guild, prefix):
        await self.bot.db.execute(
            """
            INSERT INTO meta_prefix
            VALUES (:guild_id,
                    :prefix)
            """,
            dict(guild_id=guild.id, prefix=prefix),
        )

        await self.bot.db.commit()

    async def _get_guild_prefixes(self, guild):
        async with self.bot.db.execute(
            """
            SELECT prefix
              FROM meta_prefix
             WHERE guild_id=:guild_id
            """,
            dict(guild_id=guild.id),
        ) as c:
            rows = await c.fetchall()

        return rows

    async def _remove_prefix(self, guild, prefix):
        await self.bot.db.execute(
            """
            DELETE FROM meta_prefix
             WHERE guild_id=:guild_id
               AND prefix=:prefix
            """,
            dict(guild_id=guild.id, prefix=prefix),
        )

        await self.bot.db.commit()


def setup(bot: commands.Bot):
    bot.add_cog(Meta(bot))
