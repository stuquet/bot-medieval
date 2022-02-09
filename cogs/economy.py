import discord
from discord.ext import commands


class InsufficentFundsError(Exception):
    """Exception raised when trying to do a transaction with insufficient funds."""

    def __init__(self, funds, amount):
        amount = amount if amount >= 0 else -amount
        message = f"Insufficient funds ({funds:.2f}) for amount {amount:.2f}."
        super().__init__(message)


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

        balance = await self._get_balance(member)
        await ctx.reply(f"The balance for {member.mention} is `{balance:.2f}`")

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
        times = "\n".join(
            [discord.utils.format_dt(row["time"], style="D") for row in rows]
        )
        balance = await self._get_balance(member)

        embed = (
            discord.Embed(
                title="Transaction History",
                description=f"Total Balance: {balance:.2f}",
                color=discord.Color.yellow(),
            )
            .add_field(name="Amount", value=amounts or "None", inline=True)
            .add_field(name="Description", value=descriptions or "None", inline=True)
            .add_field(name="Time", value=times or "None", inline=True)
        )
        await ctx.reply(embed=embed)

    @balance.command(name="top")
    async def balance_top(self, ctx: commands.Context):
        """List members by top balance."""

        balances = await self._get_top_balances(ctx.guild)
        members = "\n".join(
            [f"{ctx.guild.get_member(bal['member_id'])}" for bal in balances]
        )
        totals = "\n".join([f"{bal['balance']:.2f}" for bal in balances])

        embed = (
            discord.Embed(
                title="Top Balances",
                description=f"Leaderboard for {ctx.guild.name}",
                color=discord.Color.yellow(),
            )
            .add_field(name="Member", value=members, inline=True)
            .add_field(name="Balance", value=totals, inline=True)
        )
        await ctx.reply(embed=embed)

    @commands.command(aliases=["pay"])
    async def send(
        self, ctx: commands.Context, amount: float, *, to_member: discord.Member
    ):
        """Send an amount of money to the specified member.
        The amount must be above 0.
        The member cannot be yourself.
        """
        if ctx.author == to_member:
            raise commands.UserInputError("Cannot send money to self.")

        if amount <= 0:
            raise commands.UserInputError("Cannot send amounts below on equal to zero.")

        await self.transfer_money(amount, to_member, ctx.author)
        await ctx.reply(f"You sent `{amount:.2f}` to {to_member.mention}!")

    @send.error
    async def send_error(self, ctx, error):
        """Error handler for the send command."""

        error = getattr(error, "original", error)

        if isinstance(
            error,
            (commands.BadArgument, commands.UserInputError, InsufficentFundsError),
        ):
            await ctx.reply(error)

        else:
            raise error

    async def grant_money(
        self, amount: float, member: discord.Member, description="Income"
    ):
        """Helper method to grant an amount of money to a member's account."""

        await self._add_transaction(
            amount=amount, member=member, description=description
        )

    async def spend_money(
        self, amount: float, member: discord.Member, description="Spending"
    ):
        """Helper method to take an amount of money from a member's account."""

        await self._add_transaction(
            amount=-amount, member=member, description=description
        )

    async def transfer_money(
        self,
        amount: float,
        to_member: discord.Member,
        from_member: discord.Member,
        description="Money transfer",
    ):
        """Helper method to transfer an amount of money from one member's account
        to another's.
        """
        await self._add_transaction(
            amount=amount, member=to_member, description=description
        )
        await self._add_transaction(
            amount=-amount, member=from_member, description=description
        )

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
        self, *, amount: float, description: str, member: discord.Member,
    ):
        """Add a transaction to the member's account. `amount` can be negative."""

        if amount <= 0:
            current_balance = await self._get_balance(member)
            if current_balance < abs(amount):
                raise InsufficentFundsError(current_balance, amount)

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
                time=discord.utils.utcnow(),
            ),
        )

        await self.bot.db.commit()
        return last_insert_rowid

    async def _get_balance(self, member):
        async with self.bot.db.execute(
            """
            SELECT COALESCE(SUM(amount), 0) AS balance
              FROM economy_transaction
             WHERE member_id=:member_id
               AND guild_id=:guild_id
            """,
            dict(member_id=member.id, guild_id=member.guild.id),
        ) as c:
            row = await c.fetchone()

        return row["balance"]

    async def _get_top_balances(self, guild, limit=10):
        async with self.bot.db.execute(
            """
            SELECT member_id, COALESCE(SUM(amount), 0) AS balance
              FROM economy_transaction
             WHERE guild_id=:guild_id
             GROUP BY member_id
             ORDER BY balance DESC
            """,
            dict(guild_id=guild.id),
        ) as c:
            rows = await c.fetchall()

        return rows

    async def _get_transactions(self, member, limit=10):
        async with self.bot.db.execute(
            """
            SELECT amount, description, time
              FROM economy_transaction
             WHERE member_id=:member_id
               AND guild_id=:guild_id
             ORDER BY time DESC
             LIMIT :limit
            """,
            dict(member_id=member.id, guild_id=member.guild.id, limit=limit),
        ) as c:
            rows = await c.fetchall()

        return rows


def setup(bot):
    bot.add_cog(Economy(bot))
