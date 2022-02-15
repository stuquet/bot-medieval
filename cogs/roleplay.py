from pathlib import Path
import random

from discord.ext import commands

from utils.views import Confirm


ASSETS = Path("assets")


def load_text_list(path):
    with open(path) as f:
        return [line.strip() for line in f.readlines()]


class RandomMedievalNameGenerator:
    def __init__(self):
        assets_path = ASSETS / "names"
        self._female_names = load_text_list(assets_path / "female.txt")
        self._male_names = load_text_list(assets_path / "male.txt")
        self._surnames = load_text_list(assets_path / "surname.txt")
        self._titles = load_text_list(assets_path / "title.txt")

    def female_name(self):
        return random.choice(self._female_names)

    def male_name(self):
        return random.choice(self._male_names)

    def name(self):
        return random.choice(self._female_names + self._male_names)

    def surname(self):
        return random.choice(self._surnames)

    def full_name(self):
        return f"{self.name()} of {self.surname()}"

    def title(self):
        return random.choice(self._titles)

    def full_name_with_title(self):
        return f"{self.full_name()}, {self.title()}"


class Roleplay(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.random_name_generator = RandomMedievalNameGenerator()

    @commands.command()
    async def rname(self, ctx):
        """Generate a random medieval name that you can apply to yourself."""

        random_name = self.random_name_generator.full_name_with_title()
        view = Confirm()

        await ctx.reply(
            f"Do you want to change your name to __{random_name}__?", view=view
        )
        await view.wait()

        if view.value:
            await ctx.author.edit(nick=random_name)


def setup(bot):
    bot.add_cog(Roleplay(bot))
