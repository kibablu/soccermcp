import os
import soccerdata as sd
from fastmcp import FastMCP
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.requests import Request
import uvicorn
from starlette.applications import Starlette
from starlette.routing import Route

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

# Custom middleware to handle n8n's specific requirements
class N8NCompatibilityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Log incoming requests for debugging
        print(f"{request.method} {request.url.path}")
        
        # Handle n8n's POST to /sse by redirecting to /messages?session_id=init
        if request.method == "POST" and request.url.path == "/sse":
            # For n8n, we need to create a new session and redirect
            # But since we can't easily get the session ID here, we'll return a helpful error
            return JSONResponse(
                {
                    "error": "Use GET for SSE connection, or POST to /messages with a valid session_id",
                    "instructions": {
                        "sse_connection": "GET /sse",
                        "post_message": "POST /messages?session_id={session_id}"
                    }
                },
                status_code=400
            )
        
        response = await call_next(request)
        return response

if __name__ == "__main__":
    # Get the FastMCP SSE app
    app = mcp.run(
        transport="sse",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8080)),
        return_app=True  # Return the app instead of running it
    )
    
    # Add compatibility middleware
    app.add_middleware(N8NCompatibilityMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["https://klaudmazoezi.top"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add health endpoint
    @app.route("/health")
    async def health_endpoint(request):
        return JSONResponse({
            "status": "healthy",
            "service": "soccerdata-mcp",
            "version": "1.0.0",
            "endpoints": {
                "sse": "GET /sse - SSE connection endpoint",
                "messages": "POST /messages?session_id={id} - MCP message endpoint", 
                "health": "GET /health - Health check"
            }
        })
    
    @app.route("/")
    async def root_endpoint(request):
        return JSONResponse({
            "service": "Soccer Analytics MCP Server",
            "message": "MCP SSE server is running",
            "documentation": {
                "connect": "GET /sse",
                "send_message": "POST /messages?session_id={session_id}",
                "health": "GET /health"
            }
        })
    
    port = int(os.getenv("PORT", 8080))
    print(f"Starting Soccer Analytics MCP Server on port {port}")
    print(f"SSE endpoint: http://0.0.0.0:{port}/sse")
    print(f"Messages endpoint: http://0.0.0.0:{port}/messages")
    
    uvicorn.run(app, host="0.0.0.0", port=port)
