"""Main entry point for the Discord dice bot."""
import discord
from discord.ext import commands
import asyncio
import sys

from config import config
from dice_cog import setup as setup_dice


class CustomHelpCommand(commands.HelpCommand):
    """Custom help command with categorized embeds."""

    def __init__(self):
        super().__init__(
            command_attrs={
                "help": "Show this help message",
                "aliases": ["h", "commands"],
            }
        )

    def get_command_signature(self, command: commands.Command) -> str:
        return f"{self.context.clean_prefix}{command.qualified_name} {command.signature}"

    async def send_bot_help(self, mapping):
        embed = discord.Embed(
            title="🎲 Dice Bot Commands",
            description=(
                f"Prefix: `{self.context.clean_prefix}`\n"
                f"Supports: NdS notation, modifiers, keep/drop, exploding dice, compound rolls"
            ),
            color=discord.Color.blurple()
        )

        categories = {
            "🎲 Dice Rolling": ["roll", "rollstats"],
        }

        for cat_name, cmd_names in categories.items():
            cmds = []
            for name in cmd_names:
                cmd = self.context.bot.get_command(name)
                if cmd and not cmd.hidden:
                    aliases = f" ({', '.join(cmd.aliases)})" if cmd.aliases else ""
                    cmds.append(f"`{self.get_command_signature(cmd)}`{aliases} — {cmd.short_doc or 'No description'}")
            if cmds:
                embed.add_field(name=cat_name, value="\n".join(cmds), inline=False)

        embed.add_field(
            name="💡 Auto-Roll",
            value="Just type dice notation in chat (e.g., `1d6`, `2d20+5`, `4d6kh3`)",
            inline=False
        )
        embed.set_footer(text=f"Use {self.context.clean_prefix}help <command> for details")
        await self.get_destination().send(embed=embed)

    async def send_command_help(self, command: commands.Command):
        embed = discord.Embed(
            title=f"📖 {self.get_command_signature(command)}",
            description=command.help or command.short_doc or "No description available.",
            color=discord.Color.green()
        )
        if command.aliases:
            embed.add_field(name="Aliases", value=", ".join(f"`{a}`" for a in command.aliases), inline=False)
        await self.get_destination().send(embed=embed)


class DiceBot(commands.Bot):
    """Discord dice bot for RPG dice rolling."""

    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True

        super().__init__(
            command_prefix=config.prefix,
            intents=intents,
            help_command=CustomHelpCommand(),
            case_insensitive=True,
        )

    async def setup_hook(self):
        """Load cogs and sync commands."""
        await setup_dice(self)
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print("------")

    async def on_ready(self):
        """Called when bot is ready."""
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{config.prefix}help | Dice Rolling"
        )
        await self.change_presence(activity=activity)
        print(f"✅ Bot ready! Serving {len(self.guilds)} guild(s)")

    async def on_command_error(self, ctx: commands.Context, error: Exception):
        """Global error handler."""
        if isinstance(error, commands.CommandNotFound):
            return  # Ignore unknown commands

        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Missing argument: `{error.param.name}`\nUse `{config.prefix}help {ctx.command}` for usage.")
            return

        if isinstance(error, commands.BadArgument):
            await ctx.send(f"❌ Invalid argument: {error}")
            return

        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⏳ Command on cooldown. Try again in {error.retry_after:.1f}s")
            return

        # Log unexpected errors
        print(f"Error in command {ctx.command}: {error}", file=sys.stderr)
        await ctx.send("❌ An unexpected error occurred. Check console for details.")


async def main():
    """Run the bot."""
    bot = DiceBot()
    async with bot:
        await bot.start(config.discord_token)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bot stopped.")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)