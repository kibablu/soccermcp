import os
import soccerdata as sd
import pandas as pd
from fastmcp import FastMCP
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse, Response
from starlette.requests import Request
import asyncio

# 1. Environment & Cache Setup
CACHE_DIR = "/tmp/soccerdata"
os.environ["SOCCERDATA_DIR"] = CACHE_DIR
os.makedirs(CACHE_DIR, exist_ok=True)

# 2. Security Middleware (Check X-API-KEY)
class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # Allow MCP endpoints and health checks without API Key
        if request.url.path in ["/sse", "/messages", "/health", "/", "/mcp"]:
            return await call_next(request)
            
        expected_key = os.getenv("SOCCER_API_KEY", "your-fallback-key")
        provided_key = request.headers.get("X-API-KEY")
        
        if not provided_key or provided_key != expected_key:
            return JSONResponse({"error": "Unauthorized: Invalid X-API-KEY"}, status_code=401)
        
        return await call_next(request)

# 3. Initialize FastMCP Server
mcp = FastMCP("Soccer Analytics Pro")

# --- FBref Tools (Broad Stats & Results) ---

@mcp.tool()
def get_fbref_league_table(league: str, season: str) -> str:
    """Get the league standings/table from FBref."""
    try:
        fbref = sd.FBref(leagues=[league], seasons=[season])
        df = fbref.read_team_season_stats(stat_type="standard")
        return df.to_markdown()
    except Exception as e:
        return f"Error fetching FBref league table: {str(e)}"

@mcp.tool()
def get_fbref_player_stats(league: str, season: str, stat_type: str = "standard") -> str:
    """Get detailed player stats from FBref (standard, shooting, passing, etc.)"""
    try:
        fbref = sd.FBref(leagues=[league], seasons=[season])
        df = fbref.read_player_season_stats(stat_type=stat_type)
        return df.head(50).to_markdown()
    except Exception as e:
        return f"Error fetching FBref player stats: {str(e)}"

# --- Understat Tools (Advanced xG Metrics) ---

@mcp.tool()
def get_understat_xg_stats(league: str, season: str) -> str:
    """Get advanced xG and xGA stats from Understat."""
    try:
        understat = sd.Understat(leagues=[league], seasons=[season])
        df = understat.read_leagues()
        return df.to_markdown()
    except Exception as e:
        return f"Error fetching Understat xG stats: {str(e)}"

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
        return f"Error fetching Understat team xG: {str(e)}"

# --- Additional Helper Tools ---

@mcp.tool()
def get_available_leagues() -> str:
    """Get list of available leagues for reference."""
    leagues = {
        "fbref": ["ENG-Premier League", "ESP-La Liga", "ITA-Serie A", "GER-Bundesliga", "FRA-Ligue 1"],
        "understat": ["EPL", "La_liga", "Serie_A", "Bundesliga", "Ligue_1"]
    }
    return str(leagues)

if __name__ == "__main__":
    import uvicorn
    from starlette.applications import Starlette
    from starlette.routing import Route
    from mcp.server.sse import SseServerTransport
    
    # Create SSE transport
    sse = SseServerTransport("/messages")
    
    async def handle_sse(request: Request):
        """Handle SSE connection for MCP"""
        try:
            # Get the write stream from the SSE connection
            async with sse.connect_sse(
                request.scope,
                request.receive,
                request._send
            ) as streams:
                # Run the MCP server with the streams
                await mcp.run_server(
                    streams[0],  # read_stream
                    streams[1],  # write_stream
                    mcp.create_initialization_options()
                )
        except Exception as e:
            print(f"Error in SSE handler: {e}")
            return JSONResponse(
                {"error": f"SSE connection failed: {str(e)}"},
                status_code=500
            )
    
    async def handle_messages(request: Request):
        """Handle POST messages for MCP tool calls"""
        try:
            await sse.handle_post_message(
                request.scope,
                request.receive,
                request._send
            )
        except Exception as e:
            print(f"Error in messages handler: {e}")
            return JSONResponse(
                {"error": f"Message handling failed: {str(e)}"},
                status_code=500
            )
    
    async def health_endpoint(request: Request):
        """Health check endpoint"""
        return JSONResponse({
            "status": "healthy",
            "service": "soccerdata-mcp",
            "endpoints": ["/sse", "/messages", "/health"]
        })
    
    async def root_endpoint(request: Request):
        """Root endpoint with service info"""
        return JSONResponse({
            "service": "Soccer Analytics MCP Server",
            "version": "1.0.0",
            "endpoints": {
                "sse": "GET/POST - SSE connection endpoint",
                "messages": "POST - MCP message endpoint",
                "health": "GET - Health check"
            }
        })
    
    # Create the Starlette app
    app = Starlette(
        routes=[
            Route("/sse", endpoint=handle_sse, methods=["GET", "POST"]),
            Route("/messages", endpoint=handle_messages, methods=["POST"]),
            Route("/health", endpoint=health_endpoint, methods=["GET"]),
            Route("/", endpoint=root_endpoint, methods=["GET"]),
        ]
    )
    
    # Add middleware
    app.add_middleware(APIKeyMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["https://klaudmazoezi.top"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    port = int(os.getenv("PORT", 8080))
    
    print(f"Starting Soccer Analytics MCP Server on port {port}")
    print(f"SSE endpoint: http://localhost:{port}/sse (GET/POST)")
    print(f"Messages endpoint: http://localhost:{port}/messages (POST)")
    print(f"Health check: http://localhost:{port}/health")
    
    # Run the server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
