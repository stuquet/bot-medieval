from pathlib import Path
import random

import discord
from discord.ext import commands

from utils.views import Confirm


ASSETS = Path("assets")


def load_text_list(path):
    with open(path) as f:
        return [line.strip() for line in f.readlines()]


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


def setup(bot):
    bot.add_cog(Roleplay(bot))
