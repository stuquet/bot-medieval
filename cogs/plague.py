from discord.ext import commands
import discord


class Plague(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def infect(self, ctx: discord.Context, user: discord.Member):
        role = discord.utils.get(lambda r: r.name == "Plague", ctx.guild.roles)
        channel = self.bot.get_channel(1234567890)
        await user.add_roles(role)
        old_nick = user.nick
        await user.edit(nick=old_nick + "†")
        await channel.send(f"Hey {user.name}, you now have {role.name}.")

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        ctx: discord.Context,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ):

        role = discord.utils.get(lambda r: r.name == "Plague", ctx.guild.roles)

        if before.channel is None and after.channel is not None:

            if role in member.roles:
                return

            channel = after.channel
            members = channel.members

            for other_member in members:
                if role in other_member.roles:
                    await self.give_plague(ctx, member)

        else:
            return


def setup(bot: commands.Bot):
    bot.add_cog(Plague(bot))
