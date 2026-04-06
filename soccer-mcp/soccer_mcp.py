import os
import soccerdata as sd
from fastmcp import FastMCP

# 1. Environment & Cache Setup
CACHE_DIR = "/tmp/soccerdata"
os.environ["SOCCERDATA_DIR"] = CACHE_DIR
os.makedirs(CACHE_DIR, exist_ok=True)

# 2. Initialize FastMCP Server
mcp = FastMCP("Soccer Analytics Pro")

# --- FBref Tools ---

@mcp.tool()
def get_fbref_league_table(league: str, season: str) -> str:
    """Get the league standings/table from FBref."""
    try:
        fbref = sd.FBref(leagues=[league], seasons=[season])
        df = fbref.read_team_season_stats(stat_type="standard")
        return df.to_markdown()
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def get_fbref_player_stats(league: str, season: str, stat_type: str = "standard") -> str:
    """Get detailed player stats from FBref."""
    try:
        fbref = sd.FBref(leagues=[league], seasons=[season])
        df = fbref.read_player_season_stats(stat_type=stat_type)
        return df.head(50).to_markdown()
    except Exception as e:
        return f"Error: {str(e)}"

# --- Understat Tools ---

@mcp.tool()
def get_understat_xg_stats(league: str, season: str) -> str:
    """Get advanced xG and xGA stats from Understat."""
    try:
        understat = sd.Understat(leagues=[league], seasons=[season])
        df = understat.read_leagues()
        return df.to_markdown()
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def get_understat_team_xg(league: str, season: str, team_name: str = None) -> str:
    """Get team-specific xG stats from Understat."""
    try:
        understat = sd.Understat(leagues=[league], seasons=[season])
        df = understat.read_team_season_stats()
        if team_name:
            df = df[df['team_name'].str.contains(team_name, case=False)]
        return df.head(20).to_markdown()
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def get_available_leagues() -> str:
    """Get list of available leagues for reference."""
    leagues = {
        "fbref": ["ENG-Premier League", "ESP-La Liga", "ITA-Serie A", "GER-Bundesliga", "FRA-Ligue 1"],
        "understat": ["EPL", "La_liga", "Serie_A", "Bundesliga", "Ligue_1"]
    }
    return str(leagues)

if __name__ == "__main__":
    # Run with SSE transport on all interfaces
    mcp.run(
        transport="sse",
        host="0.0.0.0",  # Important: bind to all interfaces
        port=int(os.getenv("PORT", 8080))
    )
