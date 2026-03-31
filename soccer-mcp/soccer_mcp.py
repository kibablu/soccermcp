import os
import soccerdata as sd
import pandas as pd
from fastmcp import FastMCP
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from google.auth.transport.requests import Request
from google.oauth2 import id_token

# 1. Environment & Cache Setup
CACHE_DIR = "/tmp/soccerdata"
os.environ["SOCCERDATA_DIR"] = CACHE_DIR
os.makedirs(CACHE_DIR, exist_ok=True)

class CloudRunAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # Skip auth check for SSE stream endpoint to avoid interfering with long-lived connection
        # Cloud Run IAM will handle token validation at the infrastructure level
        if request.url.path == "/sse":
            return await call_next(request)
        
        # For other endpoints, validate Bearer token if present
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]
            expected_audience = os.getenv("CLOUD_RUN_AUDIENCE", os.getenv("PORT", "8080"))
            
            try:
                # Verify the ID token (optional - Cloud Run IAM can handle this too)
                id_info = id_token.verify_token(token, Request(), audience=expected_audience)
                request.state.user_info = id_info  # Attach to request if needed
            except Exception:
                # If verification fails, let Cloud Run IAM reject it (don't block here)
                pass
        
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
    # Use streamable-http transport (supports both GET for SSE + POST for messages)
    mcp.run(
        transport="streamable-http",  # ← Changed from "sse"
        host="0.0.0.0", 
        port=port,
        # Optional: customize endpoint path if needed
        # endpoint="/mcp"  # Default is "/"
    )
