from datetime import datetime

import discord
from discord.ext import commands


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.bot.loop.run_until_complete(self._create_tables())

    @commands.group(aliases=["bal", "money"])
    async def balance(self, ctx: commands.Context, *, member: discord.Member = None):
        """Show the current balance of the member.
        If no member is specified, show the balance of the command author.
        """
        pass

    @balance.command(name="history")
    async def balance_history(self, ctx, *, member: discord.Member = None):
        """Show the balance history of the member.
        If no member is specified, show the balance history of the command author.
        """
        pass

    @balance.command(name="top")
    async def balance_top(self, ctx: commands.Context):
        """List members by top balance."""

        pass

    @commands.command(name="send")
    async def send_money(
        self, ctx: commands.Context, amount: float, *, to_member: discord.Member
    ):
        """Send an amount of money to the specified member."""

        pass

    async def grant_money(self, amount: float, member: discord.Member):
        """Helper method to grant an amount of money to a member's account."""

        pass

    async def spend_money(self, amount: float, member: discord.Member):
        """Helper method to take an amount of money from a member's account."""

        pass

    async def transfer_money(
        self, amount: float, to_member: discord.Member, from_member: discord.Member
    ):
        """Helper method to transfer an amount of money from one member's account
        to another's.
        """
        pass

    async def _create_tables(self):
        """Create the necessary DB tables if they do not exist."""

        await self.bot.db.execute(
            """
            CREATE TABLE IF NOT EXISTS economy_transaction(
                amount      REAL      NOT NULL,
                description TEXT      NOT NULL,
                guild_id    INTEGER   NOT NULL,
                member_id   INTEGER   NOT NULL,
                time        TIMESTAMP NOT NULL
            )
            """
        )

        await self.bot.db.commit()

    async def _add_transaction(
        self,
        *,
        amount: float,
        description: str,
        timestamp: datetime,
        member: discord.Member
    ):
        """Add a transaction to the member's account. `amount` can be negative."""

        last_insert_rowid = await self.bot.db.execute_insert(
            """
            INSERT INTO economy_transaction
            VALUES (:amount,
                    :description,
                    :guild_id,
                    :member_id,
                    :time)
            """,
            dict(
                amount=amount,
                description=description,
                guild_id=member.guild.id,
                member_id=member.id,
                time=timestamp,
            ),
        )

        await self.bot.db.commit()
        return last_insert_rowid


def setup(bot):
    bot.add_cog(Economy(bot))
