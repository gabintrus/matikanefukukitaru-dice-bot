# 🎲 Discord Dice Bot

A feature-rich Discord bot for RPG dice rolling with support for advanced notation, probability statistics, and auto-detection of dice rolls in chat.

## ✨ Features

| Feature | Syntax Example | Description |
|---------|---------------|-------------|
| **Basic Rolls** | `1d6`, `2d20` | Roll N dice with S sides |
| **Modifiers** | `1d20+5`, `2d6-3` | Add/subtract flat modifiers |
| **Keep Highest** | `4d6kh3` | Keep highest N rolls (D&D stat rolls) |
| **Keep Lowest** | `4d6kl3` | Keep lowest N rolls |
| **Drop Highest** | `4d6dh1` | Drop highest N rolls |
| **Drop Lowest** | `4d6dl1` | Drop lowest N rolls |
| **Advantage** | `2d20kh1` | Roll with advantage (keep highest) |
| **Disadvantage** | `2d20kl1` | Roll with disadvantage (keep lowest) |
| **Exploding Dice** | `1d6!`, `1d6!5` | Re-roll on max (or custom threshold) |
| **Compound Rolls** | `2d6+1d4` | Multiple dice expressions in one roll |
| **Statistics** | `!rollstats 4d6kh3` | Probability distributions, mean, median, mode, std dev |

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- A Discord bot token ([create one here](https://discord.com/developers/applications))

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/discord-dice-bot.git
cd discord-dice-bot

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .
```

### Configuration

Copy the example environment file and add your token:

```bash
cp .env.example .env
```

Edit `.env`:
```env
DISCORD_TOKEN=your_actual_bot_token_here
PREFIX=!  # Optional, default is !
```

### Running the Bot

```bash
python bot.py
```

## 📖 Usage

### Slash Commands (Prefix: `!` by default)

| Command | Aliases | Description |
|---------|---------|-------------|
| `!roll <expression>` | `!r` | Roll dice with full notation support |
| `!rollstats <expression>` | `!rstats`, `!stats` | Show probability statistics |
| `!help` | `!h`, `!commands` | Show help message |

### Auto-Roll in Chat

Just type dice notation directly in any channel — no command needed!

```
User: I attack with 1d20+5
Bot:  🎲 Dice Roll → 1d20+5 = **18** (rolled 13 + 5)

User: Rolling stats: 4d6kh3
Bot:  🎲 Dice Roll → 4d6kh3 = **14** (kept: 6, 5, 3 | dropped: 2)
```

### Examples

```bash
# Basic rolls
!roll 1d6
!roll 2d20

# With modifiers
!roll 1d20+5
!roll 2d6-1

# D&D 5e advantage/disadvantage
!roll 2d20kh1   # Advantage
!roll 2d20kl1   # Disadvantage

# Stat generation (4d6 drop lowest)
!roll 4d6dl1
!roll 4d6kh3    # Same thing, keep highest 3

# Exploding dice (Warhammer, Savage Worlds, etc.)
!roll 1d6!      # Explode on 6
!roll 1d10!8    # Explode on 8, 9, 10

# Compound rolls
!roll 2d6+1d4   # Fireball damage + bonus
!roll 1d20+1d6+3 # Attack + damage + modifier

# Statistics
!rollstats 1d20
!rollstats 2d20kh1
!rollstats 4d6kh3
```

## 📊 Statistics Output

The `!rollstats` command provides:
- **Min/Max/Mean/Median/Mode**
- **Standard Deviation**
- **Probability Distribution** (visual bars)
- **Cumulative Probabilities**

## 🛠 Development

### Project Structure

```
discord-dice-bot/
├── bot.py           # Main entry point, bot class, error handling
├── config.py        # Configuration management (.env)
├── dice_cog.py      # Dice engine, parser, roller, statistics, embeds
├── test_regex.py    # Simple regex test for dice pattern
├── pyproject.toml   # Package metadata & dependencies
├── .env.example     # Environment template
├── .gitignore
└── LICENSE
```

### Running Tests

```bash
# Test regex parsing
python test_regex.py

# Run with pytest (if you add tests)
pytest
```

### Code Style

```bash
# Format with ruff
ruff format .

# Lint
ruff check .
```

## 📝 Dice Notation Reference

```
NdS              Roll N dice with S sides
NdS+N            Add modifier
NdS-N            Subtract modifier
NdSkhN           Keep highest N
NdSklN           Keep lowest N
NdSdhN           Drop highest N
NdSdlN           Drop lowest N
NdS!             Explode on max value
NdS!N            Explode on value N or higher
NdS+NdS          Compound expressions
```

**Limits:** Max 100 dice, max 1000 sides, max 100 explosions per die (safety limit).

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Ideas for Contributions
- Additional dice systems (FATE, Genesys, Cortex Prime)
- Roll history / logging
- Custom embed themes
- Slash command support (`/roll`)
- Web dashboard for statistics

### 💰 Donations

BTC: bc1qchu265a5m5sxhhnxmcjdk6xny96p2y43e37n6h
ETH: 0xF664dCe77af3fbeF879531dD6d29479F7370e7e6
POL: 0xF664dCe77af3fbeF879531dD6d29479F7370e7e6

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- Built with [discord.py](https://github.com/Rapptz/discord.py)
- Inspired by various tabletop RPG dice rollers
