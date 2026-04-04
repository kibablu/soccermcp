import os
import soccerdata as sd
import pandas as pd
from fastmcp import FastMCP
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

# 1. Environment & Cache Setup
CACHE_DIR = "/tmp/soccerdata"
os.environ["SOCCERDATA_DIR"] = CACHE_DIR
os.makedirs(CACHE_DIR, exist_ok=True)

# 2. Security Middleware (Check X-API-KEY)
class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # Allow the SSE handshake and health checks without API Key
        # FastMCP often uses the root or /sse for the stream
        if request.url.path in ["/", "/sse", "/health"]:
            return await call_next(request)
            
        expected_key = os.getenv("SOCCER_API_KEY", "your-fallback-key")
        provided_key = request.headers.get("X-API-KEY")
        
        if not provided_key or provided_key != expected_key:
            return JSONResponse({"error": "Unauthorized"}, status_code=401)
        
        return await call_next(request)

# 3. Initialize FastMCP Server
mcp = FastMCP("Soccer Analytics Pro")

# --- FBref Tools (Broad Stats & Results) ---

@mcp.tool()
def get_fbref_league_table(league: str, season: str) -> str:
    """Get the league standings/table from FBref."""
    fbref = sd.FBref(leagues=[league], seasons=[season])
    df = fbref.read_team_season_stats(stat_type="standard")
    return df.to_markdown()

@mcp.tool()
def get_fbref_player_stats(league: str, season: str, stat_type: str = "standard") -> str:
    """Get detailed player stats from FBref (standard, shooting, passing, etc.)"""
    fbref = sd.FBref(leagues=[league], seasons=[season])
    df = fbref.read_player_season_stats(stat_type=stat_type)
    return df.head(50).to_markdown()

# --- Understat Tools (Advanced xG Metrics) ---

@mcp.tool()
def get_understat_xg_stats(league: str, season: str) -> str:
    """Get advanced xG and xGA stats from Understat."""
    understat = sd.Understat(leagues=[league], seasons=[season])
    df = understat.read_leagues()
    return df.to_markdown()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    # Explicitly use the SSE transport. 
    # In many FastMCP versions, the default SSE path is actually the root "/"
    mcp.run(transport="sse", host="0.0.0.0", port=port)
