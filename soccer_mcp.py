# pip install fastmcp soccerdata pandas tabulate

import os
import asyncio
import soccerdata as sd
import pandas as pd
from fastmcp import FastMCP

# Define the cache directory (we'll mount the bucket here)
CACHE_DIR = os.getenv("SOCCERDATA_DIR", "/app/cache")

# Initialize FastMCP Server
mcp = FastMCP("Soccer Analytics Pro")

# --- FBref Tools (Broad Stats & Results) ---

@mcp.tool()
def get_fbref_league_table(league: str, season: str) -> str:
    """
    Get the league standings/table from FBref.
    Args:
        league: ID like 'ENG-Premier League' or 'ESP-La Liga'
        season: Year format like '2324' or '2023'
    """
    fbref = sd.FBref(leagues=[league], seasons=[season])
    # FBref's schedule often contains the standings info or use read_team_season_stats
    df = fbref.read_team_season_stats(stat_type="standard")
    return df.to_markdown()

@mcp.tool()
def get_fbref_player_stats(league: str, season: str, stat_type: str = "standard") -> str:
    """
    Get detailed player stats from FBref (shooting, passing, defense, etc.)
    stat_type options: 'standard', 'shooting', 'passing', 'passing_types', 'gca', 'defense', 'possession'
    """
    fbref = sd.FBref(leagues=[league], seasons=[season])
    df = fbref.read_player_season_stats(stat_type=stat_type)
    return df.head(50).to_markdown()  # Limiting to top 50 to save context space

# --- Understat Tools (Advanced xG Metrics) ---

@mcp.tool()
def get_understat_xg_stats(league: str, season: str) -> str:
    """
    Get advanced xG and xGA stats from Understat.
    Args:
        league: IDs like 'ENG-Premier League', 'GER-Bundesliga', 'ITA-Serie A'
        season: Year like '2023' or '2324'
    """
    understat = sd.Understat(leagues=[league], seasons=[season])
    df = understat.read_leagues()
    return df.to_markdown()

@mcp.tool()
def get_understat_shot_data(league: str, season: str) -> str:
    """
    Get shot-level data (xG per shot, situation, player) from Understat.
    """
    understat = sd.Understat(leagues=[league], seasons=[season])
    df = understat.read_shot_events()
    return df.head(30).to_markdown()

if __name__ == "__main__":
    import os
    # Get port from environment variable (Cloud Run sets this to 8080)
    port = int(os.getenv("PORT", 8080))
    # Run as a web server
    mcp.run(transport="sse", host="0.0.0.0", port=port)
