# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-XX-XX

### Added
- Initial release of Discord Dice Bot
- Full NdS dice notation support (e.g., `1d6`, `2d20`)
- Modifiers: `+N`, `-N` (e.g., `1d20+5`, `2d6-3`)
- Keep/Drop mechanics:
  - `khN` - Keep highest N (e.g., `4d6kh3` for D&D stats)
  - `klN` - Keep lowest N
  - `dhN` - Drop highest N
  - `dlN` - Drop lowest N (e.g., `4d6dl1` = drop lowest)
- Advantage/Disadvantage via `2d20kh1` / `2d20kl1`
- Exploding dice: `!` (explode on max) or `!N` (explode on N+)
- Compound expressions: `2d6+1d4`, `1d20+1d6+3`
- Probability statistics with `!rollstats`:
  - Min, Max, Mean, Median, Mode, Standard Deviation
  - Probability distribution with visual bars
  - Cumulative probabilities
- Auto-roll detection: type dice notation directly in chat
- Rich Discord embeds with roll breakdown
- Comprehensive error handling and validation
- Cooldowns on commands (3s for roll, 5s for stats)
- Configurable prefix via `.env`
- Safety limits: max 100 dice, 1000 sides, 100 explosions per die

### Technical
- Modular architecture: `DiceParser`, `DiceRoller`, `DiceStatistics`, `DiceEmbedBuilder`
- Monte Carlo simulation for complex expressions (keep/drop/explode)
- Exact probability calculation for simple expressions
- Custom help command with categorized embeds
- Global error handler with user-friendly messages

[1.0.0]: https://github.com/yourusername/discord-dice-bot/releases/tag/v1.0.0