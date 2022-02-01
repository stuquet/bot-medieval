from typing import Optional

import discord
from discord.ext import commands


class WelcomeSetupFlags(commands.FlagConverter):
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
        if guild.system_channel:
            try:
                await guild.system_channel.send(
                    f"Hello! I'm {self.bot.user.mention}!\n"
                    "You can configure a welcome message and default role for new "
                    "members with the `welcome setup` command. "
                    "I hope you will enjoy having me in your server :)"
                )
            except discord.Forbidden:
                print(
                    "Unable to send message to system channel of guild "
                    f"{guild.name} ({guild.id})"
                )

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

    @commands.group(invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def welcome(self, ctx):
        """Parent command for the welcoming functionality.
        Invoke without subcommand to list the current configuration.

        You must have Administrator permissions to use this command.
        """
        row = await self._get_welcome_data(ctx.guild)

        if row:
            data = dict(
                role=ctx.guild.get_role(row["default_role_id"]),
                channel=ctx.guild.get_channel(row["welcome_channel_id"]),
                message=row["welcome_message"],
            )
            content = self._format_welcome_confirmation(data)
            if content:
                return await ctx.reply(content)

        await ctx.reply(
            "You did not configure the welcome feature yet. Look at "
            f"`{ctx.prefix}help welcome setup` for tips."
        )

    @welcome.command(name="setup")
    @commands.has_permissions(administrator=True)
    async def welcome_setup(self, ctx: commands.Context, *, flags: WelcomeSetupFlags):
        """Setup the data needed for the welcome feature.
        You can use as many flags as wanted, specifying a particular flag will
        overwrite what is currently configured. Reset the config with `welcome reset`.

        Flags:
            channel: The channel to send the welcome messages to. Channel name, ID
                     or mention work.
            message: The content of the message to be sent.
                alias: content
            role: The default role to add to every new member.

        You must have the Administrator permission to use this command.
        """
        content = self._format_welcome_confirmation(
            dict(role=flags.role, channel=flags.channel, message=flags.message)
        )
        if content:
            await ctx.reply(content)
        else:
            await ctx.reply(
                "You did not provide any values. Look at "
                f"`{ctx.prefix}help welcome setup` for tips."
            )
        await self._update_welcome_data(ctx.guild, flags)

    @welcome.command(name="reset")
    @commands.has_permissions(administrator=True)
    async def welcome_reset(self, ctx: commands.Context):
        """Reset the welcome data for the guild.

        You must have Administrator permission to use this command.
        """
        await ctx.reply(
            "Removing all welcome configuration. You can run the "
            f"`{ctx.prefix}welcome setup` command again to enter new values."
        )
        await self._remove_welcome_data(ctx.guild)

    @welcome.error
    @welcome_setup.error
    @welcome_reset.error
    async def welcome_error(self, ctx, error):
        """Error handler for the welcome command group."""

        if isinstance(error, (commands.RoleNotFound, commands.ChannelNotFound)):
            await ctx.reply(error)

        else:
            raise error

    def _format_welcome_confirmation(self, data: dict):
        content = ""
        if data["role"]:
            content += f"Default role: {data['role'].mention}.\n"
        if data["channel"]:
            content += f"Welcome channel: {data['channel'].mention}.\n"
        if data["message"]:
            content += f"Welcome message:\n```\n{data['message']}\n```\n"

        return content

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

    async def _update_welcome_data(self, guild, flags):
        await self.bot.db.execute(
            """
            INSERT INTO welcome_data
            VALUES (:default_role_id,
                    :guild_id,
                    :welcome_channel_id,
                    :welcome_message)
                ON CONFLICT(guild_id) DO
            UPDATE
               SET default_role_id = COALESCE(:default_role_id, default_role_id),
                   welcome_channel_id = COALESCE(:welcome_channel_id,
                        welcome_channel_id),
                   welcome_message = COALESCE(:welcome_message, welcome_message)
             WHERE guild_id = :guild_id
            """,
            dict(
                guild_id=guild.id,
                default_role_id=flags.role.id if flags.role else None,
                welcome_channel_id=flags.channel.id if flags.channel else None,
                welcome_message=flags.message,
            ),
        )

        await self.bot.db.commit()

    async def _remove_welcome_data(self, guild):
        await self.bot.db.execute(
            """
            DELETE FROM welcome_data
             WHERE guild_id = :guild_id
            """,
            dict(guild_id=guild.id),
        )

        await self.bot.db.commit()


def setup(bot):
    bot.add_cog(Welcome(bot))
