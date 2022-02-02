from datetime import datetime

import discord
from discord.ext import commands


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.bot.loop.run_until_complete(self._create_tables())

    @commands.group(aliases=["bal", "money"], invoke_without_command=True)
    async def balance(self, ctx: commands.Context, *, member: discord.Member = None):
        """Show the current balance of the member.
        If no member is specified, show the balance of the command author.
        """
        if member is None:
            member = ctx.author

        row = await self._get_balance(member)
        await ctx.reply(f"The balance for {member.mention} is `{row['balance']:.2f}`")

    @balance.command(name="history")
    async def balance_history(self, ctx, *, member: discord.Member = None):
        """Show the balance history of the member.
        If no member is specified, show the balance history of the command author.
        """
        if member is None:
            member = ctx.author

        rows = await self._get_transactions(member)
        amounts = "\n".join([f"{row['amount']:.2f}" for row in rows])
        descriptions = "\n".join([row["description"] for row in rows])
        times = "\n".join([discord.utils.format_dt(row["time"]) for row in rows])
        row = await self._get_balance(member)
        balance = row["balance"]

        embed = (
            discord.Embed(
                title="Transaction History",
                description=f"Total Balance: {balance:.2f}",
                color=discord.Color.yellow(),
            )
            .add_field(name="Amount", value=amounts, inline=True)
            .add_field(name="Description", value=descriptions, inline=True)
            .add_field(name="Time", value=times, inline=True)
        )
        await ctx.reply(embed=embed)

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
        member: discord.Member,
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

    async def _get_balance(self, member):
        async with self.bot.db.execute(
            """
            SELECT SUM(amount) AS balance
              FROM economy_transaction
             WHERE member_id=:member_id
            """,
            dict(member_id=member.id),
        ) as c:
            row = await c.fetchone()

        return row

    async def _get_transactions(self, member, limit=10):
        async with self.bot.db.execute(
            """
            SELECT amount, description, time
              FROM economy_transaction
             WHERE member_id=:member_id
             ORDER BY time DESC
             LIMIT :limit
            """,
            dict(member_id=member.id, limit=limit),
        ) as c:
            rows = await c.fetchall()

        return rows


def setup(bot):
    bot.add_cog(Economy(bot))
