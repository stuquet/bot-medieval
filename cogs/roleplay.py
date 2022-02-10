from pathlib import Path
import random

from discord.ext import commands


ASSETS = Path("assets")


def load_text_list(path):
    with open(path) as f:
        return [line.strip() for line in f.readlines()]


class RandomMedievalNameGenerator:
    def __init__(self):
        self._female_names = load_text_list(ASSETS / "names" / "female.txt")
        self._male_names = load_text_list(ASSETS / "names" / "male.txt")
        self._surnames = load_text_list(ASSETS / "names" / "surname.txt")
        self._titles = load_text_list(ASSETS / "names" / "title.txt")

    def female_name(self):
        return random.choice(self._female_names)

    def male_name(self):
        return random.choice(self._male_names)

    def name(self):
        return random.choice(self._female_names + self._male_names)

    def surname(self):
        return random.choice(self._surnames)

    def title(self):
        return random.choice(self._titles)

    def full_name_with_title(self):
        return f"{self.title()} {self.name()} of {self.surname()}"


class Roleplay(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.random_name_generator = RandomMedievalNameGenerator()

    @commands.command()
    async def rname(self, ctx):
        """Generate a random medieval name that you can apply to yourself."""

        await ctx.reply(self.random_name_generator.full_name_with_title())


def setup(bot):
    bot.add_cog(Roleplay(bot))
