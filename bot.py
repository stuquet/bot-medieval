import aiosqlite
import discord
from discord.ext import commands

from private.config import token


class MedievalBot(commands.Bot):
    """Subclass of the commands.Bot class.
    This class add functionality such as a database connection,
    global event handlers, and other utilities.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Make DB connection
        self.db = self.loop.run_until_complete(
            create_db_connection(kwargs.get("db_name", ":memory:"))
        )

    async def close(self):
        """Close the necessary connections before closing the bot."""

        await self.db.close()
        await super().close()

    async def on_ready(self):
        permissions = discord.Permissions.text()
        url = discord.utils.oauth_url(self.user.id, permissions=permissions)
        print(
            f"Logged in as {self.user.name} (ID:{self.user.id})\n"
            f"Connected to {len(self.guilds)} guilds\n"
            f"Connected to {len(set(self.get_all_members()))} users\n"
            "--------\n"
            f"Current Discord.py Version: {discord.__version__}\n"
            "--------\n"
            f"Invite {self.user.name} with the following link:\n"
            f"{url}\n"
            "--------\n"
        )


async def create_db_connection(db_name):
    """Create the connection to the SQLite database."""

    db = await aiosqlite.connect(db_name, detect_types=1)  # 1: parse declared types
    db.row_factory = aiosqlite.Row  # allow for name-based access of data columns
    await db.execute("PRAGMA foreign_keys = ON")  # allow for cascade deletion
    return db


# see https://youtu.be/g_wlZ9IhbTs
def main():
    intents = discord.Intents.default()
    intents.members = True

    bot = MedievalBot(command_prefix=commands.when_mentioned_or("!"), intents=intents)

    cogs = ["cogs.meta", "cogs.plague", "cogs.welcome"]
    for cog in cogs:
        bot.load_extension(cog)

    bot.run(token)


if __name__ == "__main__":
    main()
