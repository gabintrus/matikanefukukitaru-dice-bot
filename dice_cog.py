"""
Dice Cog for Discord Bot - RPG Dice Roller

Supports NdS notation with advanced features:
- Basic rolls: 1d6, 2d20
- Modifiers: 1d20+5, 2d6-3
- Keep/Drop: 4d6kh3, 4d6kl3, 4d6dh1, 4d6dl1
- Advantage/Disadvantage: 2d20kh1, 2d20kl1
- Exploding dice: 1d6!, 1d6!5
- Compound rolls: 2d6+1d4
"""

import re
import random
import math
from dataclasses import dataclass, field
from typing import Optional, List, Tuple, Union
from collections import Counter

import discord
from discord.ext import commands
from discord import app_commands


@dataclass
class DieRoll:
    """Represents a single die roll with metadata."""
    value: int
    kept: bool = True
    exploded: bool = False
    original_value: Optional[int] = None  # For exploded dice, the original roll


@dataclass
class DiceExpression:
    """Represents a parsed dice expression (e.g., 2d6kh1+3)."""
    num_dice: int
    sides: int
    keep_highest: Optional[int] = None
    keep_lowest: Optional[int] = None
    drop_highest: Optional[int] = None
    drop_lowest: Optional[int] = None
    explode_on: Optional[int] = None  # None = no explode, value = explode on this value or higher
    modifier: int = 0
    rolls: List[DieRoll] = field(default_factory=list)

    @property
    def total(self) -> int:
        """Calculate total of kept rolls plus modifier."""
        kept_values = [r.value for r in self.rolls if r.kept]
        return sum(kept_values) + self.modifier

    @property
    def kept_rolls(self) -> List[DieRoll]:
        return [r for r in self.rolls if r.kept]

    @property
    def dropped_rolls(self) -> List[DieRoll]:
        return [r for r in self.rolls if not r.kept]


class DiceParser:
    """Parses dice notation strings into DiceExpression objects."""

    # Regex for a single dice expression: NdS[kh/kl/dh/dlN][!][N][+/-N]
    DICE_PATTERN = re.compile(
        r'(?P<num>\d+)d(?P<sides>\d+)'
        r'(?:'
        r'(?:kh(?P<kh>\d+))|'      # keep highest
        r'(?:kl(?P<kl>\d+))|'      # keep lowest
        r'(?:dh(?P<dh>\d+))|'      # drop highest
        r'(?:dl(?P<dl>\d+))'       # drop lowest
        r')?'
        r'(?:!(?P<explode>\d*))?'   # exploding dice
        r'(?P<mod>[+-]\d+)?'        # modifier
    )

    @classmethod
    def parse(cls, expression: str) -> List[DiceExpression]:
        """
        Parse a dice expression string into a list of DiceExpression objects.
        Handles compound expressions like "2d6+1d4-3" and modifiers like "1d20+5".
        """
        expression = expression.strip().lower().replace(' ', '')
        if not expression:
            raise ValueError("Empty dice expression")

        # Split expression into parts by + and - that are BETWEEN dice expressions
        parts = cls._split_compound(expression)

        if not parts:
            raise ValueError("No valid dice expressions found")

        expressions = []

        for part in parts:
            match = cls.DICE_PATTERN.fullmatch(part)
            if not match:
                raise ValueError(f"Invalid dice notation: {part}")

            num_dice = int(match.group('num'))
            sides = int(match.group('sides'))

            if num_dice <= 0:
                raise ValueError("Number of dice must be positive")
            if sides <= 0:
                raise ValueError("Number of sides must be positive")
            if num_dice > 100:
                raise ValueError("Too many dice (max 100)")
            if sides > 1000:
                raise ValueError("Too many sides (max 1000)")

            # Parse keep/drop
            kh = match.group('kh')
            kl = match.group('kl')
            dh = match.group('dh')
            dl = match.group('dl')

            keep_highest = int(kh) if kh else None
            keep_lowest = int(kl) if kl else None
            drop_highest = int(dh) if dh else None
            drop_lowest = int(dl) if dl else None

            # Validate keep/drop
            keep_drop_count = sum(1 for x in [kh, kl, dh, dl] if x)
            if keep_drop_count > 1:
                raise ValueError("Cannot combine keep and drop options")

            if keep_highest is not None:
                if keep_highest > num_dice:
                    raise ValueError(f"Cannot keep highest {keep_highest} from {num_dice} dice")
            if keep_lowest is not None:
                if keep_lowest > num_dice:
                    raise ValueError(f"Cannot keep lowest {keep_lowest} from {num_dice} dice")
            if drop_highest is not None:
                if drop_highest >= num_dice:
                    raise ValueError(f"Cannot drop highest {drop_highest} from {num_dice} dice")
            if drop_lowest is not None:
                if drop_lowest >= num_dice:
                    raise ValueError(f"Cannot drop lowest {drop_lowest} from {num_dice} dice")

            # Parse exploding
            explode_str = match.group('explode')
            explode_on = None
            if explode_str is not None:
                if explode_str == '':
                    explode_on = sides  # Explode on max value
                else:
                    explode_on = int(explode_str)
                    if explode_on < 2 or explode_on > sides:
                        raise ValueError(f"Explode value must be between 2 and {sides}")

            # Parse modifier (from the dice expression itself)
            mod_str = match.group('mod')
            modifier = int(mod_str) if mod_str else 0

            expr = DiceExpression(
                num_dice=num_dice,
                sides=sides,
                keep_highest=keep_highest,
                keep_lowest=keep_lowest,
                drop_highest=drop_highest,
                drop_lowest=drop_lowest,
                explode_on=explode_on,
                modifier=modifier
            )
            expressions.append(expr)

        if not expressions:
            raise ValueError("No valid dice expressions found")

        return expressions

    @classmethod
    def _split_compound(cls, expression: str) -> List[str]:
        """
        Split compound expressions like '2d6+1d4-3' into ['2d6', '+1d4', '-3'].
        Handles cases where +N is a modifier vs +NdM is a separator.
        """
        # Strategy: parse sequentially. Find each dice expression by trying to parse
        # from each dice core position, and use the successfully parsed length.
        dice_core_pattern = re.compile(r'(\d+)d(\d+)')
        cores = list(dice_core_pattern.finditer(expression))

        if not cores:
            return [expression]

        if len(cores) == 1:
            return [expression]

        parts = []
        pos = 0

        for i, core in enumerate(cores):
            # Skip any whitespace/operators before this core
            while pos < core.start() and expression[pos] in ' +-':
                pos += 1

            if pos < core.start():
                # There's something unexpected, include it
                pos = core.start()

            # Try to parse a dice expression starting at pos
            # Find how much of the string from pos constitutes a valid dice expression
            remaining = expression[pos:]
            part = cls._extract_single_expression(remaining)

            if part:
                parts.append(part)
                pos += len(part)
            else:
                # Fallback: just use the core
                parts.append(core.group(0))
                pos = core.end()

        return parts

    @classmethod
    def _extract_single_expression(cls, s: str) -> str:
        """Extract a single valid dice expression from the start of string s."""
        # The expression pattern: NdS[kh/kl/dh/dlN][!N][+/-N]
        # We need to match the modifier ONLY if it's NOT followed by another dice expression (d\d+)
        # Use negative lookahead: (?![d]) to ensure +N is not followed by 'd'

        pattern = re.compile(
            r'^(\d+d\d+)'
            r'(?:'
            r'(?:kh|kl|dh|dl)\d+'
            r')?'
            r'(?:!\d*)?'
            r'(?:[+-]\d+(?!d))?'
        )

        match = pattern.match(s)
        if match:
            return match.group(0)
        return ""


class DiceRoller:
    """Handles rolling dice according to parsed expressions."""

    MAX_EXPLOSIONS = 100  # Safety limit for exploding dice

    @classmethod
    def roll_expression(cls, expr: DiceExpression) -> DiceExpression:
        """Roll dice for a single expression."""
        rolls = []

        for _ in range(expr.num_dice):
            roll = cls._roll_single_die(expr.sides, expr.explode_on)
            rolls.append(roll)

        expr.rolls = rolls
        cls._apply_keep_drop(expr)
        return expr

    @classmethod
    def _roll_single_die(cls, sides: int, explode_on: Optional[int]) -> DieRoll:
        """Roll a single die, handling explosions."""
        total_value = 0
        original_value = None
        exploded = False
        explosion_count = 0

        while True:
            value = random.randint(1, sides)

            if original_value is None:
                original_value = value

            total_value += value

            # Check for explosion
            if explode_on is not None and value >= explode_on:
                exploded = True
                explosion_count += 1
                if explosion_count >= cls.MAX_EXPLOSIONS:
                    break
                continue
            break

        return DieRoll(
            value=total_value,
            kept=True,
            exploded=exploded,
            original_value=original_value if exploded else None
        )

    @classmethod
    def _apply_keep_drop(cls, expr: DiceExpression) -> None:
        """Apply keep/drop rules to the rolls."""
        if not expr.rolls:
            return

        # Sort rolls by value (keep original indices for reference)
        indexed_rolls = list(enumerate(expr.rolls))
        indexed_rolls.sort(key=lambda x: x[1].value)

        # Determine which to keep
        keep_indices = set()

        if expr.keep_highest is not None:
            # Keep highest N
            for i in range(expr.keep_highest):
                keep_indices.add(indexed_rolls[-(i + 1)][0])
        elif expr.keep_lowest is not None:
            # Keep lowest N
            for i in range(expr.keep_lowest):
                keep_indices.add(indexed_rolls[i][0])
        elif expr.drop_highest is not None:
            # Drop highest N (keep the rest)
            for i in range(expr.num_dice - expr.drop_highest):
                keep_indices.add(indexed_rolls[i][0])
        elif expr.drop_lowest is not None:
            # Drop lowest N (keep the rest)
            for i in range(expr.drop_lowest, expr.num_dice):
                keep_indices.add(indexed_rolls[i][0])
        else:
            # Keep all
            keep_indices = set(range(expr.num_dice))

        # Apply kept/dropped status
        for i, roll in enumerate(expr.rolls):
            roll.kept = i in keep_indices


class DiceStatistics:
    """Calculates statistics for dice expressions."""

    @classmethod
    def calculate(cls, expressions: List[DiceExpression]) -> dict:
        """
        Calculate statistics for one or more dice expressions.
        Uses exact calculation for simple expressions, Monte Carlo for complex ones.
        """
        # Start with a distribution of just 0
        distribution = Counter({0: 1})
        total_combinations = 1

        for expr in expressions:
            expr_dist, expr_combos = cls._expression_distribution(expr)

            # Convolve distributions
            new_dist = Counter()
            for val1, count1 in distribution.items():
                for val2, count2 in expr_dist.items():
                    new_dist[val1 + val2] += count1 * count2

            distribution = new_dist
            total_combinations *= expr_combos

        # Calculate statistics
        values = []
        for val, count in distribution.items():
            values.extend([val] * count)

        values.sort()
        n = len(values)

        return {
            'min': min(values),
            'max': max(values),
            'mean': sum(values) / n,
            'median': values[n // 2] if n % 2 == 1 else (values[n // 2 - 1] + values[n // 2]) / 2,
            'mode': max(distribution.items(), key=lambda x: x[1])[0],
            'std_dev': math.sqrt(sum((v - sum(values)/n)**2 for v in values) / n),
            'distribution': dict(sorted(distribution.items())),
            'total_combinations': total_combinations
        }

    @classmethod
    def _expression_distribution(cls, expr: DiceExpression) -> Tuple[Counter, int]:
        """Get probability distribution for a single expression (without modifiers)."""
        # This is a simplified version - for exact stats with keep/drop/explode,
        # we'd need more complex computation. We'll approximate for now.

        if expr.keep_highest or expr.keep_lowest or expr.drop_highest or expr.drop_lowest or expr.explode_on:
            # For complex expressions, use Monte Carlo simulation
            return cls._monte_carlo_distribution(expr)

        # Simple NdS distribution
        dist = Counter()
        for _ in range(expr.num_dice):
            new_dist = Counter()
            for val, count in dist.items() if dist else [(0, 1)]:
                for face in range(1, expr.sides + 1):
                    new_dist[val + face] += count
            dist = new_dist

        combos = expr.sides ** expr.num_dice

        # Apply modifier
        if expr.modifier != 0:
            new_dist = Counter()
            for val, count in dist.items():
                new_dist[val + expr.modifier] += count
            dist = new_dist

        return dist, combos

    @classmethod
    def _monte_carlo_distribution(cls, expr: DiceExpression, trials: int = 50000) -> Tuple[Counter, int]:
        """Approximate distribution using Monte Carlo simulation."""
        dist = Counter()

        for _ in range(trials):
            test_expr = DiceExpression(
                num_dice=expr.num_dice,
                sides=expr.sides,
                keep_highest=expr.keep_highest,
                keep_lowest=expr.keep_lowest,
                drop_highest=expr.drop_highest,
                drop_lowest=expr.drop_lowest,
                explode_on=expr.explode_on,
                modifier=expr.modifier
            )
            DiceRoller.roll_expression(test_expr)
            dist[test_expr.total] += 1

        return dist, trials


class DiceEmbedBuilder:
    """Builds rich Discord embeds for dice roll results."""

    @staticmethod
    def build_roll_embed(
        original_expression: str,
        expressions: List[DiceExpression],
        author: discord.User,
        show_stats: bool = False,
        simple: bool = False
    ) -> discord.Embed:
        """Build an embed for a dice roll result."""
        total = sum(expr.total for expr in expressions)

        # Determine color based on result (green for good, red for bad, yellow for neutral)
        color = discord.Color.gold()

        embed = discord.Embed(
            title="🎲 Dice Roll",
            description=f"`{original_expression}`",
            color=color,
            timestamp=discord.utils.utcnow()
        )

        embed.set_author(
            name=author.display_name,
            icon_url=author.display_avatar.url
        )

        if simple:
            # Simple output: just the total
            embed.add_field(
                name="🎯 **Result**",
                value=f"# {total}",
                inline=False
            )
        else:
            # Build roll details
            details = []
            for i, expr in enumerate(expressions):
                if len(expressions) > 1:
                    details.append(f"**Expression {i + 1}:** `{expr.num_dice}d{expr.sides}`")
                else:
                    details.append(f"**Dice:** `{expr.num_dice}d{expr.sides}`")

                # Show keep/drop/explode modifiers
                mods = []
                if expr.keep_highest:
                    mods.append(f"kh{expr.keep_highest}")
                if expr.keep_lowest:
                    mods.append(f"kl{expr.keep_lowest}")
                if expr.drop_highest:
                    mods.append(f"dh{expr.drop_highest}")
                if expr.drop_lowest:
                    mods.append(f"dl{expr.drop_lowest}")
                if expr.explode_on:
                    if expr.explode_on == expr.sides:
                        mods.append("!")
                    else:
                        mods.append(f"!{expr.explode_on}")
                if expr.modifier != 0:
                    mods.append(f"{expr.modifier:+d}")

                if mods:
                    details.append(f"**Modifiers:** `{' '.join(mods)}`")

                # Show individual rolls
                roll_strs = []
                for roll in expr.rolls:
                    if roll.exploded:
                        if roll.original_value is not None:
                            roll_strs.append(f"**{roll.value}** ⟵ `({roll.original_value} + ...)` 💥")
                        else:
                            roll_strs.append(f"**{roll.value}** 💥")
                    elif roll.kept:
                        roll_strs.append(f"**{roll.value}**")
                    else:
                        roll_strs.append(f"~~{roll.value}~~")

                details.append(f"**Rolls:** {' '.join(roll_strs)}")

                if expr.modifier != 0:
                    details.append(f"**Modifier:** `{expr.modifier:+d}`")

                details.append(f"**Subtotal:** `{expr.total}`")
                details.append("")  # Empty line between expressions

            embed.add_field(
                name="Details",
                value="\n".join(details).strip(),
                inline=False
            )

            # Total
            embed.add_field(
                name="🎯 **Total**",
                value=f"# {total}",
                inline=False
            )

        # Statistics if requested
        if show_stats:
            stats = DiceStatistics.calculate(expressions)
            stats_text = (
                f"Min: **{stats['min']}** | "
                f"Max: **{stats['max']}** | "
                f"Avg: **{stats['mean']:.2f}** | "
                f"Median: **{stats['median']:.1f}** | "
                f"Mode: **{stats['mode']}** | "
                f"StdDev: **{stats['std_dev']:.2f}**"
            )
            embed.add_field(
                name="📊 Statistics",
                value=stats_text,
                inline=False
            )

        embed.set_footer(text="Dice Roller • Use !rollstats for detailed probabilities")

        return embed

    @staticmethod
    def build_stats_embed(
        original_expression: str,
        expressions: List[DiceExpression],
        author: discord.User
    ) -> discord.Embed:
        """Build an embed with detailed probability statistics."""
        stats = DiceStatistics.calculate(expressions)

        embed = discord.Embed(
            title="📊 Dice Probability Statistics",
            description=f"`{original_expression}`",
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow()
        )

        embed.set_author(
            name=author.display_name,
            icon_url=author.display_avatar.url
        )

        # Basic stats
        embed.add_field(
            name="Basic Statistics",
            value=(
                f"**Minimum:** {stats['min']}\n"
                f"**Maximum:** {stats['max']}\n"
                f"**Mean (Average):** {stats['mean']:.2f}\n"
                f"**Median:** {stats['median']:.1f}\n"
                f"**Mode (Most Likely):** {stats['mode']}\n"
                f"**Standard Deviation:** {stats['std_dev']:.2f}"
            ),
            inline=True
        )

        # Distribution (top 20 most likely outcomes)
        dist_items = sorted(stats['distribution'].items(), key=lambda x: -x[1])[:20]
        dist_text = []
        total_combos = stats['total_combinations']

        for value, count in dist_items:
            prob = (count / total_combos) * 100
            bar_length = int(prob / 2)  # Scale for visual bar
            bar = "█" * min(bar_length, 20)
            dist_text.append(f"`{value:3d}` | {prob:5.2f}% {bar}")

        embed.add_field(
            name="Probability Distribution (Top 20)",
            value="```\n" + "\n".join(dist_text) + "\n```",
            inline=False
        )

        # Cumulative probabilities
        sorted_dist = sorted(stats['distribution'].items())
        cum_text = []
        cumulative = 0

        for value, count in sorted_dist:
            cumulative += count
            cum_prob = (cumulative / total_combos) * 100
            cum_text.append(f"≤ `{value:3d}`: {cum_prob:5.2f}%")

        embed.add_field(
            name="Cumulative Probabilities",
            value="```\n" + "\n".join(cum_text) + "\n```",
            inline=False
        )

        embed.set_footer(text=f"Based on {total_combos:,} combinations" if total_combos < 1000000 else f"Monte Carlo simulation ({total_combos:,} trials)")

        return embed

    @staticmethod
    def build_error_embed(error_message: str, author: discord.User) -> discord.Embed:
        """Build an embed for error messages."""
        embed = discord.Embed(
            title="❌ Dice Roll Error",
            description=error_message,
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_author(
            name=author.display_name,
            icon_url=author.display_avatar.url
        )
        embed.set_footer(text="Examples: 1d6, 2d20+5, 4d6kh3, 1d6!, 2d6+1d4")
        return embed


class DiceCog(commands.Cog):
    """Cog for handling dice rolls in Discord."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Regex to detect dice notation in messages (e.g., 1d6, 2d20+5)
        # Matches: NdS followed by optional modifiers (kh/kl/dh/dl, !, +/-N), optionally followed by +NdS...
        # The parser handles splitting compound expressions
        self.dice_pattern = re.compile(
            r'(?<!\w)(?P<dice>\d+d\d+(?:[^a-z\s]*(?:[a-z]+\d+)?(?:!\d*)?(?:[+-]\d+)?)?)',
            re.IGNORECASE
        )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Listen for dice notation in messages and auto-roll."""
        # Ignore bot messages and commands
        if message.author.bot:
            return

        # Ignore if it's a command (starts with prefix)
        ctx = await self.bot.get_context(message)
        if ctx.valid:
            return

        # Check for dice notation
        match = self.dice_pattern.search(message.content)
        if not match:
            return

        dice_notation = match.group('dice')

        # Avoid rolling for very long expressions (likely not dice)
        if len(dice_notation) > 100:
            return

        try:
            await self._process_roll(message, dice_notation, auto=True)
        except Exception as e:
            # Silently ignore errors in auto-roll to not spam
            pass

    @commands.command(name="roll", aliases=["r"])
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def roll_command(self, ctx: commands.Context, *, expression: str):
        """Roll dice using NdS notation.

        Examples:
        - `!roll 1d6` - Roll one 6-sided die
        - `!roll 2d20+5` - Roll two d20s and add 5
        - `!roll 4d6kh3` - Roll 4d6, keep highest 3 (stat roll)
        - `!roll 2d20kh1` - Roll with advantage (keep highest 1)
        - `!roll 2d20kl1` - Roll with disadvantage (keep lowest 1)
        - `!roll 1d6!` - Exploding die (re-roll on max)
        - `!roll 1d6!5` - Explode on 5 or 6
        - `!roll 2d6+1d4` - Compound roll
        """
        await self._process_roll(ctx.message, expression, auto=False)

    @commands.command(name="rollstats", aliases=["rstats", "stats"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def rollstats_command(self, ctx: commands.Context, *, expression: str):
        """Show probability statistics for a dice expression.

        Examples:
        - `!rollstats 1d6` - Statistics for a d6
        - `!rollstats 2d20kh1` - Statistics for advantage
        - `!rollstats 4d6kh3` - Statistics for D&D stat rolls
        """
        try:
            expressions = DiceParser.parse(expression)
        except ValueError as e:
            embed = DiceEmbedBuilder.build_error_embed(str(e), ctx.author)
            await ctx.send(embed=embed)
            return

        embed = DiceEmbedBuilder.build_stats_embed(expression, expressions, ctx.author)
        await ctx.send(embed=embed)

    async def _process_roll(self, message: discord.Message, expression: str, auto: bool = False):
        """Process a dice roll and send the result."""
        try:
            expressions = DiceParser.parse(expression)
        except ValueError as e:
            if not auto:
                embed = DiceEmbedBuilder.build_error_embed(str(e), message.author)
                await message.reply(embed=embed, mention_author=False)
            return

        # Roll all expressions
        for expr in expressions:
            DiceRoller.roll_expression(expr)

        # Build and send embed
        # Use simple output for explicit commands (!roll), detailed for auto-rolls
        embed = DiceEmbedBuilder.build_roll_embed(expression, expressions, message.author, simple=not auto)

        if auto:
            # For auto-rolls, reply to the message
            await message.reply(embed=embed, mention_author=False)
        else:
            # For explicit commands, send normally
            await message.channel.send(embed=embed)

    @roll_command.error
    @rollstats_command.error
    async def roll_error(self, ctx: commands.Context, error: commands.CommandError):
        """Handle command errors."""
        if isinstance(error, commands.CommandOnCooldown):
            embed = DiceEmbedBuilder.build_error_embed(
                f"⏳ Cooldown! Try again in {error.retry_after:.1f} seconds.",
                ctx.author
            )
            await ctx.send(embed=embed, delete_after=5)
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = DiceEmbedBuilder.build_error_embed(
                "Usage: `!roll <expression>` (e.g., `!roll 2d6+3`)",
                ctx.author
            )
            await ctx.send(embed=embed)
        else:
            # Log unexpected errors
            self.bot.logger.error(f"Dice command error: {error}")
            embed = DiceEmbedBuilder.build_error_embed(
                "An unexpected error occurred. Please try again.",
                ctx.author
            )
            await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    """Setup function to add the cog to the bot."""
    await bot.add_cog(DiceCog(bot))