"""Configuration management for the Discord dice bot."""
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    """Bot configuration loaded from environment variables."""
    discord_token: str
    prefix: str = "!"

    @classmethod
    def from_env(cls) -> "Config":
        """Create config from environment variables."""
        token = os.getenv("DISCORD_TOKEN")
        if not token or token == "your_discord_bot_token_here":
            raise ValueError(
                "DISCORD_TOKEN not set! Please edit .env with your Discord bot token.\n"
                "Get one at: https://discord.com/developers/applications"
            )

        return cls(
            discord_token=token,
            prefix=os.getenv("PREFIX", "!"),
        )


config = Config.from_env()