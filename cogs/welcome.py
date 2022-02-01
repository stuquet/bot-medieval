from typing import Optional

import discord
from discord.ext import commands


class WelcomeDataFlags(commands.FlagConverter):
    channel: Optional[discord.TextChannel]
    role: Optional[discord.Role]
    message: Optional[str] = commands.flag(aliases=["content"])


class Welcome(commands.Cog):
    """Collection of commands and events regarding for welcoming new members."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

        self.bot.loop.run_until_complete(self._create_tables())

    @commands.Cog.listener("on_guild_join")
    async def send_setup_request(self, guild: discord.Guild):
        """Send a message in the system channel to ask an Administrator to run the
        setup command.
        """
        pass

    @commands.Cog.listener("on_member_join")
    async def on_member_join(self, member: discord.Member):
        """Run the events for new members."""

        guild = member.guild
        # get role and message from DB
        data = await self._get_welcome_data(guild)
        role_id = data["default_role_id"]
        channel_id = data["welcome_channel_id"]
        message = data["welcome_message"]

        channel = guild.get_channel(channel_id) or guild.system_channel
        role = guild.get_role(role_id)

        if message and channel:
            await self.send_welcome_message(member, channel, message)

        if role:
            await self.add_default_role(member, role)

    async def send_welcome_message(
        self, member: discord.Member, channel: discord.TextChannel, message: str
    ):
        """Send the configurated welcome message to the system channel."""

        await channel.send(message)

    async def add_default_role(self, member: discord.Member, role: discord.Role):
        """Add the configurated default role to the new member."""

        await member.add_roles(role)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setup(self, ctx: commands.Context, *, flags: WelcomeDataFlags):
        """Setup the data needed for the welcome feature.

        Flags:
            channel:
            message:
                alias: content
            role:

        You must have the Administrator permission to use this command.
        """
        print(flags)

    async def _create_tables(self):
        """Create the necessary DB tables if they do not exist."""

        await self.bot.db.execute(
            """
            CREATE TABLE IF NOT EXISTS welcome_data(
                default_role_id    INTEGER,
                guild_id           INTEGER NOT NULL UNIQUE,
                welcome_channel_id INTEGER,
                welcome_message    TEXT
            )
            """
        )

        await self.bot.db.commit()

    async def _get_welcome_data(self, guild):
        """Get the welcome message and default role from the database."""

        async with self.bot.db.execute(
            """
            SELECT *
              FROM welcome_data
             WHERE guild_id = :guild_id
            """,
            dict(guild_id=guild.id),
        ) as c:
            row = await c.fetchone()

        return row


def setup(bot):
    bot.add_cog(Welcome(bot))
