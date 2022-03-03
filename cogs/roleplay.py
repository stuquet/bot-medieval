from collections import defaultdict
from datetime import datetime, timedelta, timezone
import io
from pathlib import Path
import random

import discord
from discord.utils import snowflake_time
from discord.ext import commands
import matplotlib.pyplot as plt
import numpy as np

from utils.views import Confirm

ASSETS = Path("assets")


def load_text_list(path):
    with open(path) as f:
        return [line.strip() for line in f.readlines()]


def _get_next_level_xp(level):
    return 5 * level ** 2 + 50 * level + 100


def _get_level_from_xp(xp):
    remaining_xp = xp
    level = 0

    while remaining_xp >= (_xp := _get_next_level_xp(level)):
        remaining_xp -= _xp
        level += 1

    return level, remaining_xp


def make_rank_history_graph(history):
    data = [[snowflake_time(row["message_id"]), row["xp"]] for row in history]
    data.sort(key=lambda x: x[0])
    time, xp = zip(*data)

    fig, ax = plt.subplots()
    ax.plot(time, np.cumsum(xp))
    ax.set_xlabel("Date")
    ax.tick_params(axis="x", rotation=45)
    ax.set_ylabel("Experience")

    graph = io.BytesIO()
    fig.savefig(graph, format="png")
    graph.seek(0)

    return graph


class RandomMedievalNameGenerator:
    _assets_path = ASSETS / "names"
    _female_names = load_text_list(_assets_path / "female.txt")
    _male_names = load_text_list(_assets_path / "male.txt")
    _surnames = load_text_list(_assets_path / "surname.txt")
    _titles = load_text_list(_assets_path / "title.txt")

    @classmethod
    def female_name(cls):
        return random.choice(cls._female_names)

    @classmethod
    def male_name(cls):
        return random.choice(cls._male_names)

    @classmethod
    def name(cls):
        return random.choice(cls._female_names + cls._male_names)

    @classmethod
    def surname(cls):
        return random.choice(cls._surnames)

    @classmethod
    def full_name(cls):
        return f"{cls.name()} of {cls.surname()}"

    @classmethod
    def title(cls):
        return random.choice(cls._titles)

    @classmethod
    def full_name_with_title(cls):
        return f"{cls.full_name()}, {cls.title()}"


class Roleplay(commands.Cog):
    """Collections of commands and utilities for medieval roleplay features."""

    def __init__(self, bot):
        self.bot = bot
        self._last_message = defaultdict(
            lambda: datetime.min.replace(tzinfo=timezone.utc)
        )

        self.bot.loop.run_until_complete(self._create_tables())

    def get_last_message(self, member):
        return self._last_message[(member.guild.id, member.id)]

    def set_last_message(self, message):
        self._last_message[(message.guild.id, message.author.id)] = message.created_at

    @commands.command()
    async def rname(self, ctx):
        """Generate a random medieval name that you can apply to yourself."""

        random_name = RandomMedievalNameGenerator.full_name_with_title()
        view = Confirm()

        await ctx.reply(
            f"Do you want to change your name to __{random_name}__?", view=view
        )
        await view.wait()

        if view.value:
            try:
                await ctx.author.edit(nick=random_name)

            except discord.Forbidden:
                # ignore if author's top role is above the bot's
                pass

    @commands.Cog.listener(name="on_message")
    async def level_add_xp(self, message):
        guild, member = message.guild, message.author

        if guild is None:
            # do not count experience in DMs
            return

        if member == guild.me:
            # do not count the bot
            return

        ctx = await self.bot.get_context(message)
        if ctx.command:
            # do not count command invocations
            return

        last_message = self.get_last_message(member)
        if message.created_at - last_message < timedelta(minutes=1):
            # message experience cooldown
            return

        # if all checks, add experience to member
        experience = await self._get_experience(member)
        level, _ = _get_level_from_xp(experience)
        xp = random.randint(15, 25)
        # print(f"Adding {xp} xp to member {member} in guild {guild}")
        await self._add_experience(message, xp)
        self.set_last_message(message)

        # Check if level up
        new_level, _ = _get_level_from_xp(experience + xp)
        if new_level != level:
            print("Level up!")

    @commands.group(aliases=["level", "lvl"], invoke_without_command=True)
    async def rank(self, ctx, *, member: discord.Member = None):
        """Show the level and progress of the member."""

        if member is None:
            member = ctx.author

        embed = await self._rank_embed(member)

        await ctx.reply(embed=embed)

    @rank.command(name="history")
    async def rank_history(self, ctx, *, member: discord.Member = None):
        """Show the level progress over time of the member."""

        if member is None:
            member = ctx.author

        rows = await self._get_experience(member)
        embed = await self._rank_embed(member, rows)
        filename = "rank_history.png"
        embed.set_image(url=f"attachment://{filename}")

        graph = await self.bot.loop.run_in_executor(None, make_rank_history_graph, rows)

        await ctx.reply(embed=embed, file=discord.File(graph, filename=filename))

    async def _rank_embed(self, member, rows=None):
        if rows is None:
            rows = await self._get_experience(member)

        experience = sum([row["xp"] for row in rows])
        level, remaining_xp = _get_level_from_xp(experience)
        next_level_xp = _get_next_level_xp(level)
        # xp_until_next_level = next_level_xp - remaining_xp
        # multiple of 10
        percent_progress = int(round(remaining_xp / next_level_xp * 100, -1))

        if percent_progress <= 25:
            filled = "🟥"
        elif 25 < percent_progress <= 50:
            filled = "🟧"
        elif 50 < percent_progress <= 75:
            filled = "🟨"
        elif 75 < percent_progress:
            filled = "🟩"

        # white or black? "⬜" "⬛"
        progress_10 = percent_progress // 10
        # add zero-width-space so it renders fine on mobile
        progress = "\u200B" + filled * progress_10 + "⬛" * (10 - progress_10)

        _user = await self.bot.fetch_user(member.id)
        embed = (
            discord.Embed(
                title=f"Rank for {member.display_name}",
                color=_user.accent_color or member.color,
            )
            .add_field(name=f"Level {level}", value=f"{remaining_xp}/{next_level_xp}")
            .add_field(name="Total experience", value=experience)
            .add_field(name="Progress", value=progress, inline=False)
            .set_thumbnail(url=member.avatar.url)
        )

        return embed

    async def _create_tables(self):
        """Create the necessary DB tables if they do not exist."""

        await self.bot.db.execute(
            """
            CREATE TABLE IF NOT EXISTS roleplay_experience(
                guild_id    INTEGER NOT NULL,
                member_id   INTEGER NOT NULL,
                message_id  INTEGER NOT NULL,
                xp          INTEGER NOT NULL
            )
            """
        )

        await self.bot.db.commit()

    async def _add_experience(self, message, xp):
        await self.bot.db.execute(
            """
            INSERT INTO roleplay_experience
            VALUES (:guild_id,
                    :member_id,
                    :message_id,
                    :xp)
            """,
            dict(
                guild_id=message.guild.id,
                member_id=message.author.id,
                message_id=message.id,
                xp=xp,
            ),
        )

        await self.bot.db.commit()

    async def _get_experience(self, member):
        async with self.bot.db.execute(
            """
            SELECT message_id, xp
              FROM roleplay_experience
             WHERE member_id=:member_id
               AND guild_id=:guild_id
            """,
            dict(guild_id=member.guild.id, member_id=member.id,),
        ) as c:
            rows = await c.fetchall()

        return rows


def setup(bot):
    bot.add_cog(Roleplay(bot))
