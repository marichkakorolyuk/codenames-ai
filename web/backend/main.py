from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import logging
import os
import json
import asyncio
import random
import uuid
from datetime import datetime
import sys

# Add the parent directory to sys.path to import game_core
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from game_core import GameEngine, CardType, Card, GameState
from words import WORD_LIST

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(f"logs/api_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("codenames-api")

# Initialize the app
app = FastAPI(title="Codenames Game API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# Initialize game engine
game_engine = GameEngine(WORD_LIST)

# In-memory storage for active connections and games
connected_clients = {}
games = {}
active_players = {}

# Models for request/response data
class GameCreationRequest(BaseModel):
    first_team: Optional[str] = None  # If not provided, will be random

class PlayerJoinRequest(BaseModel):
    game_id: str
    player_name: str
    team: str  # "red" or "blue"
    role: str  # "spymaster" or "operative"
    ai_controlled: bool = False

class ClueRequest(BaseModel):
    game_id: str
    player_id: str
    clue_word: str
    clue_number: int

class GuessRequest(BaseModel):
    game_id: str
    player_id: str
    guess_word: str

class EndTurnRequest(BaseModel):
    game_id: str
    player_id: str

# Helper functions for game management
def get_card_type_enum(type_str: str) -> CardType:
    """Convert string card type to CardType enum"""
    if type_str.lower() == "red":
        return CardType.RED
    elif type_str.lower() == "blue":
        return CardType.BLUE
    elif type_str.lower() == "neutral":
        return CardType.NEUTRAL
    elif type_str.lower() == "assassin":
        return CardType.ASSASSIN
    else:
        raise ValueError(f"Invalid card type: {type_str}")

async def broadcast_game_state(game_id: str):
    """Broadcast game state to all connected clients for a game"""
    if game_id not in games:
        return

    game = game_engine.get_game(game_id)
    if not game:
        return

    # Get players for this game
    game_players = {pid: player for pid, player in active_players.items() if player.get("game_id") == game_id}
    
    # Send appropriate game state to each player
    for player_id, player_info in game_players.items():
        if player_id in connected_clients:
            websocket = connected_clients[player_id]
            
            # Determine which view to send based on player role
            team = get_card_type_enum(player_info["team"])
            if player_info["role"] == "spymaster":
                state = game.get_spymaster_state(team)
            else:
                state = game.get_visible_state(team)
                
            # Add additional game info
            state["current_player"] = {
                "name": player_info["name"],
                "team": player_info["team"],
                "role": player_info["role"]
            }
            
            try:
                await websocket.send_json({
                    "type": "game_state_update",
                    "data": state
                })
            except Exception as e:
                logger.error(f"Error sending game state to {player_id}: {str(e)}")

# API Endpoints
@app.get("/")
async def root():
    return {"message": "Codenames Game API"}

@app.post("/games")
async def create_game(request: GameCreationRequest):
    """Create a new game"""
    try:
        game_id = game_engine.create_game()
        game = game_engine.get_game(game_id)
        
        # If first team is specified, override the random selection
        if request.first_team:
            try:
                first_team = get_card_type_enum(request.first_team)
                game.current_team = first_team
            except ValueError:
                pass  # If invalid, keep the random team
        
        # Store game info
        games[game_id] = {
            "created_at": datetime.now().isoformat(),
            "players": {}
        }
        
        logger.info(f"Created new game: {game_id}")
        return {
            "game_id": game_id,
            "first_team": game.current_team.value
        }
    except Exception as e:
        logger.error(f"Error creating game: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/games/{game_id}")
async def get_game(game_id: str):
    """Get basic info about a game"""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game = game_engine.get_game(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found in engine")
    
    return {
        "game_id": game_id,
        "created_at": games[game_id]["created_at"],
        "current_team": game.current_team.value,
        "players": games[game_id]["players"],
        "status": "active" if not game.winner else "completed",
        "winner": game.winner.value if game.winner else None
    }

@app.post("/games/{game_id}/join")
async def join_game(game_id: str, request: PlayerJoinRequest):
    """Join a game as a player"""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    try:
        # Generate a unique player ID
        player_id = str(uuid.uuid4())
        
        # Store player info
        player_info = {
            "id": player_id,
            "name": request.player_name,
            "team": request.team.lower(),
            "role": request.role.lower(),
            "ai_controlled": request.ai_controlled,
            "game_id": game_id
        }
        
        active_players[player_id] = player_info
        games[game_id]["players"][player_id] = player_info
        
        logger.info(f"Player {request.player_name} joined game {game_id} as {request.team} {request.role}")
        
        return {
            "player_id": player_id,
            "game_id": game_id,
            **player_info
        }
    except Exception as e:
        logger.error(f"Error joining game: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/games/{game_id}/clue")
async def give_clue(game_id: str, request: ClueRequest):
    """Give a clue as a spymaster"""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    if request.player_id not in active_players:
        raise HTTPException(status_code=404, detail="Player not found")
    
    player = active_players[request.player_id]
    if player["role"] != "spymaster":
        raise HTTPException(status_code=403, detail="Only spymasters can give clues")
    
    try:
        # Get the player's team
        team = get_card_type_enum(player["team"])
        
        # Process the clue
        success = game_engine.process_clue(
            game_id, 
            request.clue_word, 
            request.clue_number, 
            team
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Invalid clue or not your turn")
        
        logger.info(f"Clue given in game {game_id}: {request.clue_word} {request.clue_number}")
        
        # Broadcast updated game state to all clients
        await broadcast_game_state(game_id)
        
        return {"success": True}
    except Exception as e:
        logger.error(f"Error giving clue: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/games/{game_id}/guess")
async def make_guess(game_id: str, request: GuessRequest):
    """Make a guess as an operative"""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    if request.player_id not in active_players:
        raise HTTPException(status_code=404, detail="Player not found")
    
    player = active_players[request.player_id]
    if player["role"] != "operative":
        raise HTTPException(status_code=403, detail="Only operatives can make guesses")
    
    try:
        # Get the player's team
        team = get_card_type_enum(player["team"])
        
        # Process the guess
        result = game_engine.process_guess(game_id, request.guess_word, team)
        
        if not result:
            raise HTTPException(status_code=400, detail="Invalid guess or not your turn")
        
        if not result.get("success", False):
            raise HTTPException(status_code=400, detail=result.get("error", "Unknown error"))
        
        logger.info(f"Guess made in game {game_id}: {request.guess_word} - Result: {result}")
        
        # Broadcast updated game state to all clients
        await broadcast_game_state(game_id)
        
        return result
    except Exception as e:
        logger.error(f"Error making guess: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/games/{game_id}/end-turn")
async def end_turn(game_id: str, request: EndTurnRequest):
    """End the current turn"""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    if request.player_id not in active_players:
        raise HTTPException(status_code=404, detail="Player not found")
    
    player = active_players[request.player_id]
    
    try:
        # Get the player's team
        team = get_card_type_enum(player["team"])
        
        # End the turn
        success = game_engine.end_turn(game_id, team)
        
        if not success:
            raise HTTPException(status_code=400, detail="Cannot end turn or not your turn")
        
        logger.info(f"Turn ended in game {game_id} by {player['name']}")
        
        # Broadcast updated game state to all clients
        await broadcast_game_state(game_id)
        
        return {"success": True}
    except Exception as e:
        logger.error(f"Error ending turn: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket connection for real-time updates
@app.websocket("/ws/{player_id}")
async def websocket_endpoint(websocket: WebSocket, player_id: str):
    if player_id not in active_players:
        await websocket.close(code=1008, reason="Player not found")
        return
    
    await websocket.accept()
    connected_clients[player_id] = websocket
    
    game_id = active_players[player_id]["game_id"]
    logger.info(f"WebSocket connection established for player {player_id} in game {game_id}")
    
    try:
        # Send initial game state
        await broadcast_game_state(game_id)
        
        # Keep connection alive and handle incoming messages
        while True:
            data = await websocket.receive_text()
            # Currently, we don't expect any client-initiated messages
            # but we could handle them here if needed
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for player {player_id}")
    except Exception as e:
        logger.error(f"WebSocket error for player {player_id}: {str(e)}")
    finally:
        if player_id in connected_clients:
            del connected_clients[player_id]

if __name__ == "__main__":
    import uvicorn
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    uvicorn.run(app, host="0.0.0.0", port=8000)
