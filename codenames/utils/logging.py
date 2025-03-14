"""
Logging utilities for Codenames AI.
Provides structured logging for game sessions, AI decisions, and debug information.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional


class GameLogger:
    """Logger for game sessions and AI decisions"""
    
    def __init__(self, log_dir: str = "logs", log_level: int = logging.INFO):
        """
        Initialize the logger.
        
        Args:
            log_dir: Directory to store log files
            log_level: Logging level (from the logging module)
        """
        self.log_dir = log_dir
        
        # Create log directory if it doesn't exist
        os.makedirs(log_dir, exist_ok=True)
        
        # Set up logger
        self.logger = logging.getLogger("codenames")
        self.logger.setLevel(log_level)
        
        # Clear any existing handlers to avoid duplicates
        if self.logger.hasHandlers():
            self.logger.handlers.clear()
        
        # Create a file handler for the log
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(log_dir, f"game_{timestamp}.log")
        file_handler = logging.FileHandler(log_file)
        
        # Create a console handler
        console_handler = logging.StreamHandler()
        
        # Create a formatter and add it to the handlers
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add the handlers to the logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # Store game events for later saving
        self.game_id = None
        self.game_events = []
    
    def start_game(self, game_id: str, config: Dict[str, Any]) -> None:
        """
        Log the start of a new game.
        
        Args:
            game_id: Unique identifier for the game
            config: Game configuration
        """
        self.game_id = game_id
        self.game_events = []
        
        event = {
            "type": "game_start",
            "timestamp": datetime.now().isoformat(),
            "game_id": game_id,
            "config": config
        }
        
        self.game_events.append(event)
        self.logger.info(f"Game {game_id} started with config: {json.dumps(config)}")
    
    def log_clue(self, team: str, clue: str, number: int, targets: list = None) -> None:
        """
        Log a clue given by a spymaster.
        
        Args:
            team: Team of the spymaster (red/blue)
            clue: The clue word
            number: The clue number
            targets: Target words the spymaster intended (if AI)
        """
        event = {
            "type": "clue",
            "timestamp": datetime.now().isoformat(),
            "game_id": self.game_id,
            "team": team,
            "clue": clue,
            "number": number,
            "targets": targets
        }
        
        self.game_events.append(event)
        target_str = f", targets: {targets}" if targets else ""
        self.logger.info(f"Clue from {team}: '{clue}' {number}{target_str}")
    
    def log_guess(self, team: str, word: str, result: Dict[str, Any]) -> None:
        """
        Log a guess made by an operative.
        
        Args:
            team: Team of the operative (red/blue)
            word: The guessed word
            result: Result of the guess (success, card type, etc.)
        """
        event = {
            "type": "guess",
            "timestamp": datetime.now().isoformat(),
            "game_id": self.game_id,
            "team": team,
            "word": word,
            "result": result
        }
        
        self.game_events.append(event)
        self.logger.info(f"Guess from {team}: '{word}', result: {json.dumps(result)}")
    
    def log_turn_end(self, team: str, reason: str) -> None:
        """
        Log the end of a team's turn.
        
        Args:
            team: Team whose turn ended (red/blue)
            reason: Reason for ending the turn
        """
        event = {
            "type": "turn_end",
            "timestamp": datetime.now().isoformat(),
            "game_id": self.game_id,
            "team": team,
            "reason": reason
        }
        
        self.game_events.append(event)
        self.logger.info(f"Turn ended for {team}: {reason}")
    
    def log_game_end(self, winner: str, game_state: Dict[str, Any]) -> None:
        """
        Log the end of the game.
        
        Args:
            winner: Winning team (red/blue)
            game_state: Final game state
        """
        event = {
            "type": "game_end",
            "timestamp": datetime.now().isoformat(),
            "game_id": self.game_id,
            "winner": winner,
            "turns": game_state.get("turn_count", 0),
            "final_state": game_state
        }
        
        self.game_events.append(event)
        self.logger.info(f"Game {self.game_id} ended. Winner: {winner}")
        
        # Save the complete game log to a JSON file
        self._save_game_log()
    
    def log_ai_decision(self, agent_name: str, decision_type: str, data: Dict[str, Any]) -> None:
        """
        Log an AI decision for analysis.
        
        Args:
            agent_name: Name of the AI agent
            decision_type: Type of decision (clue, guess, debate, etc.)
            data: Decision data including input, output, and reasoning
        """
        event = {
            "type": "ai_decision",
            "timestamp": datetime.now().isoformat(),
            "game_id": self.game_id,
            "agent": agent_name,
            "decision_type": decision_type,
            "data": data
        }
        
        self.game_events.append(event)
        
        # Log a condensed version to the standard log
        if "reasoning" in data:
            shortened = data["reasoning"][:100] + "..." if len(data["reasoning"]) > 100 else data["reasoning"]
            self.logger.info(f"AI {agent_name} {decision_type}: {shortened}")
        else:
            self.logger.info(f"AI {agent_name} made a {decision_type} decision")
    
    def _save_game_log(self) -> None:
        """Save the full game log to a JSON file"""
        if not self.game_id:
            return
            
        game_log_dir = os.path.join(self.log_dir, "game_logs")
        os.makedirs(game_log_dir, exist_ok=True)
        
        log_file = os.path.join(game_log_dir, f"game_{self.game_id}.json")
        
        with open(log_file, 'w') as f:
            json.dump(self.game_events, f, indent=2)
        
        self.logger.info(f"Complete game log saved to {log_file}")


# Global logger instance
game_logger = GameLogger()


def get_logger() -> GameLogger:
    """Get the global logger instance"""
    return game_logger
