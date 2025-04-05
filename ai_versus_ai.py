#!/usr/bin/env python3
"""
Codenames AI vs AI Game Observer
Allows observing AI agents playing against each other with configurable models and detailed logging.
"""

import os
import sys
import random
import time
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import openai
from game_core import GameEngine, CardType, Card, GameState
from words import WORD_LIST

class PlayerRole:
    SPYMASTER = "spymaster"
    OPERATIVE = "operative"

class Team:
    RED = CardType.RED
    BLUE = CardType.BLUE

class AIPlayer:
    def __init__(self, name: str, role: str, team: CardType, model: str = "gpt-4o"):
        self.name = name
        self.role = role  # "spymaster" or "operative"
        self.team = team  # CardType.RED or CardType.BLUE
        self.model = model
        self.decisions: List[Dict[str, Any]] = []  # Track all decisions for analysis

class GameLogger:
    def __init__(self, log_dir: str = "logs"):
        """Initialize the game logger"""
        self.log_dir = log_dir
        self.game_log = []
        self.summary_stats = {
            "red_wins": 0,
            "blue_wins": 0,
            "game_duration": 0,
            "total_turns": 0,
            "red_team": {"correct_guesses": 0, "wrong_guesses": 0},
            "blue_team": {"correct_guesses": 0, "wrong_guesses": 0},
            "clues": [],  # Will store all clues and their related guesses
        }
        
        # Create log directory if it doesn't exist
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
    
    def log_event(self, event_type: str, details: Dict[str, Any]):
        """Log a game event"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = {
            "timestamp": timestamp,
            "type": event_type,
            "details": details
        }
        self.game_log.append(log_entry)
        
        # Print event to console with timestamp
        timestamp_display = f"[{timestamp}]"
        if event_type == "game_start":
            print(f"\n{timestamp_display} ===== NEW GAME STARTED =====")
            print(f"{timestamp_display} Red Team: {details['red_team']['spymaster']} (Spymaster) and {details['red_team']['operative']} (Operative)")
            print(f"{timestamp_display} Blue Team: {details['blue_team']['spymaster']} (Spymaster) and {details['blue_team']['operative']} (Operative)")
        elif event_type == "board_state":
            print(f"\n{timestamp_display} ----- GAME BOARD -----")
            print(f"{timestamp_display} RED: {details['red_remaining']} left | BLUE: {details['blue_remaining']} left")
            print(f"{timestamp_display} Current turn: {details['current_team'].upper()}")
            self._print_board(details['board'], details['for_spymaster'])
        elif event_type == "clue":
            print(f"\n{timestamp_display} {details['team'].upper()} SPYMASTER GIVES CLUE: \"{details['word']}\" for {details['number']}")
        elif event_type == "guess":
            print(f"{timestamp_display} {details['team'].upper()} OPERATIVE GUESSES: \"{details['word']}\" - {details['result']}")
        elif event_type == "turn_end":
            print(f"\n{timestamp_display} Turn ends for {details['team'].upper()} team")
        elif event_type == "game_end":
            print(f"\n{timestamp_display} ===== GAME OVER - {details['winner'].upper()} TEAM WINS =====")
            print(f"{timestamp_display} Total turns: {details['total_turns']}")
    
    def _print_board(self, board: List[Dict], for_spymaster: bool = False):
        """Print the game board in a readable format"""
        print()
        for i in range(5):
            row = []
            for j in range(5):
                card = board[i * 5 + j]
                if card['revealed']:
                    # Show revealed cards with their type
                    card_display = f"{card['word'].ljust(12)} ({card['type']})"
                elif for_spymaster:
                    # Show unrevealed cards with their type for spymaster
                    card_display = f"{card['word'].ljust(12)} ({card['type']})"
                else:
                    # Show only the word for operatives
                    card_display = card['word'].ljust(12)
                row.append(card_display)
            print(" | ".join(row))
        print()
    
    def update_stats(self, stats_update: Dict[str, Any]):
        """Update the game statistics"""
        for key, value in stats_update.items():
            if key in self.summary_stats:
                if isinstance(self.summary_stats[key], dict) and isinstance(value, dict):
                    # Update nested dictionaries
                    for nested_key, nested_value in value.items():
                        if nested_key in self.summary_stats[key]:
                            self.summary_stats[key][nested_key] += nested_value
                else:
                    # Update simple values
                    self.summary_stats[key] += value
    
    def log_clue(self, team: str, clue_word: str, clue_number: int, model: str, target_words: List[str] = None):
        """Log a clue and create a tracking entry for related guesses"""
        # Ensure we always have a valid list for target_words
        if target_words is None:
            target_words = []
        
        # Ensure number is consistent with targets if we have targets
        actual_number = clue_number
        if target_words and clue_number != len(target_words):
            if len(target_words) > 0:
                actual_number = len(target_words)
            else:
                target_words = ["(Not specified)"] * clue_number
        
        clue_entry = {
            "team": team,
            "clue_word": clue_word,
            "clue_number": actual_number,
            "model": model,
            "target_words": target_words,
            "guesses": [],
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.summary_stats["clues"].append(clue_entry)
        return len(self.summary_stats["clues"]) - 1  # Return index of this clue for tracking guesses
    
    def log_guess(self, clue_index: int, guess_word: str, actual_type: str, is_correct: bool, model: str):
        """Log a guess associated with a specific clue"""
        if 0 <= clue_index < len(self.summary_stats["clues"]):
            guess_entry = {
                "word": guess_word,
                "actual_type": actual_type,
                "is_correct": is_correct,
                "model": model,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            self.summary_stats["clues"][clue_index]["guesses"].append(guess_entry)
    
    def generate_markdown_report(self, game_id: str, config: Dict[str, Any]) -> str:
        """Generate a markdown report of the game"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        total_games = self.summary_stats["red_wins"] + self.summary_stats["blue_wins"]
        
        # Calculate game duration in minutes and seconds
        game_duration_seconds = self.summary_stats["game_duration"] / max(total_games, 1)
        minutes = int(game_duration_seconds // 60)
        seconds = int(game_duration_seconds % 60)
        
        md = [
            f"# Codenames AI vs AI Game Report",
            f"**Generated:** {timestamp}",
            f"**Game ID:** {game_id}",
            "",
            "## Game Configuration",
            f"- Red Spymaster Model: {config.get('red_spymaster_model', 'gpt-4o')}",
            f"- Red Operative Model: {config.get('red_operative_model', 'gpt-4o')}",
            f"- Blue Spymaster Model: {config.get('blue_spymaster_model', 'gpt-4o')}",
            f"- Blue Operative Model: {config.get('blue_operative_model', 'gpt-4o')}",
            "",
            "## Game Summary",
            f"- Date/Time: {timestamp}",
            f"- Game Duration: {minutes}m {seconds}s",
            f"- Red Wins: {self.summary_stats['red_wins']}/{total_games} ({self.summary_stats['red_wins']/max(total_games, 1)*100:.1f}%)",
            f"- Blue Wins: {self.summary_stats['blue_wins']}/{total_games} ({self.summary_stats['blue_wins']/max(total_games, 1)*100:.1f}%)",
            f"- Average Game Duration: {self.summary_stats['game_duration']/max(total_games, 1):.2f} seconds",
            f"- Average Turns Per Game: {self.summary_stats['total_turns']/max(total_games, 1):.2f}",
            "",
            "## Team Performance",
            "",
            "### Red Team",
            "| Metric | Value |",
            "| ------ | ----- |",
        ]
        
        # Red team stats
        red_correct = self.summary_stats['red_team']['correct_guesses']
        red_wrong = self.summary_stats['red_team']['wrong_guesses']
        red_total = red_correct + red_wrong
        red_accuracy = red_correct / max(red_total, 1) * 100
        md.extend([
            f"| Correct Guesses | {red_correct} |",
            f"| Wrong Guesses | {red_wrong} |",
            f"| Total Guesses | {red_total} |",
            f"| Accuracy | {red_accuracy:.2f}% |",
            "",
            "### Blue Team",
            "| Metric | Value |",
            "| ------ | ----- |",
        ])
        
        # Blue team stats
        blue_correct = self.summary_stats['blue_team']['correct_guesses']
        blue_wrong = self.summary_stats['blue_team']['wrong_guesses']
        blue_total = blue_correct + blue_wrong
        blue_accuracy = blue_correct / max(blue_total, 1) * 100
        md.extend([
            f"| Correct Guesses | {blue_correct} |",
            f"| Wrong Guesses | {blue_wrong} |",
            f"| Total Guesses | {blue_total} |",
            f"| Accuracy | {blue_accuracy:.2f}% |",
            "",
            "## Clue and Guess Analysis",
            "",
        ])
        
        # Clue-by-clue analysis
        if self.summary_stats["clues"]:
            md.append("| Time | Team | Clue | Number | Intended Targets | Guessed Word | Actual Card Type | Correct? |")
            md.append("| ---- | ---- | ---- | ------ | --------------- | ------------ | ---------------- | -------- |")
            
            for clue_entry in self.summary_stats["clues"]:
                team = clue_entry["team"].upper()
                clue_word = clue_entry["clue_word"]
                clue_number = clue_entry["clue_number"]
                clue_time = clue_entry.get("timestamp", "")
                
                # Format the intended targets
                targets = clue_entry.get("target_words", [])
                if not targets:
                    # Ensure we never show "Unknown" in reports
                    target_count = max(1, clue_number)
                    targets_str = f"({target_count} unspecified targets)"
                else:
                    targets_str = ", ".join(targets)
                
                if clue_entry["guesses"]:
                    # First guess row includes the clue and targets
                    first_guess = clue_entry["guesses"][0]
                    guess_time = first_guess.get("timestamp", "")
                    md.append(f"| {clue_time} | {team} | {clue_word} | {clue_number} | {targets_str} | {first_guess['word']} | {first_guess['actual_type'].upper()} | {'✓' if first_guess['is_correct'] else '✗'} |")
                    
                    # Subsequent guesses for this clue
                    for guess in clue_entry["guesses"][1:]:
                        guess_time = guess.get("timestamp", "")
                        md.append(f"| {guess_time} | | | | | {guess['word']} | {guess['actual_type'].upper()} | {'✓' if guess['is_correct'] else '✗'} |")
                else:
                    # Clue with no guesses
                    md.append(f"| {clue_time} | {team} | {clue_word} | {clue_number} | {targets_str} | No guesses | | |")
        else:
            md.append("No clues were recorded in this game.")
        
        # Add a timeline section
        md.extend([
            "",
            "## Game Timeline",
            "",
            "| Timestamp | Event | Details |",
            "| --------- | ----- | ------- |",
        ])
        
        for entry in self.game_log:
            event_time = entry.get("timestamp", "")
            event_type = entry.get("type", "")
            details = entry.get("details", {})
            
            # Format details based on event type
            if event_type == "game_start":
                details_str = f"Game started with {details.get('red_team', {}).get('spymaster', '')} and {details.get('blue_team', {}).get('spymaster', '')} as spymasters"
            elif event_type == "clue":
                details_str = f"{details.get('team', '').upper()} Spymaster gave clue: \"{details.get('word', '')}\" for {details.get('number', '')}"
            elif event_type == "guess":
                details_str = f"{details.get('team', '').upper()} Operative guessed: \"{details.get('word', '')}\" - {details.get('result', '')}"
            elif event_type == "turn_end":
                details_str = f"Turn ended for {details.get('team', '').upper()} team ({details.get('reason', '')})"
            elif event_type == "game_end":
                details_str = f"Game over - {details.get('winner', '').upper()} team wins after {details.get('total_turns', '')} turns"
            else:
                details_str = str(details)
            
            md.append(f"| {event_time} | {event_type} | {details_str} |")
        
        return "\n".join(md)
    
    def save_markdown_report(self, game_id: str, config: Dict[str, Any]):
        """Generate and save a markdown report of the game"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"{self.log_dir}/report_{game_id}_{timestamp}.md"
        
        report_content = self.generate_markdown_report(game_id, config)
        
        with open(report_filename, 'w') as f:
            f.write(report_content)
        
        print(f"\nDetailed game report saved to {report_filename}")
    
    def save_logs(self, game_id: str, config: Dict[str, Any]):
        """Save the game logs, stats, and markdown report to files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"{self.log_dir}/game_{game_id}_{timestamp}.json"
        stats_filename = f"{self.log_dir}/stats_{timestamp}.json"
        
        # Save detailed game log
        with open(log_filename, 'w') as f:
            json.dump(self.game_log, f, indent=2)
        
        # Save or update stats
        try:
            # Try to load existing stats file
            if os.path.exists(stats_filename):
                with open(stats_filename, 'r') as f:
                    existing_stats = json.load(f)
                
                # Merge stats
                for key, value in self.summary_stats.items():
                    if key in existing_stats:
                        if isinstance(existing_stats[key], dict) and isinstance(value, dict):
                            for nested_key, nested_value in value.items():
                                if nested_key in existing_stats[key]:
                                    existing_stats[key][nested_key] += nested_value
                        elif key == "clues" and isinstance(value, list):
                            # For clues, we append the new clues to the existing list
                            existing_stats[key].extend(value)
                        else:
                            existing_stats[key] += value
                    else:
                        existing_stats[key] = value
                
                # Write updated stats
                with open(stats_filename, 'w') as f:
                    json.dump(existing_stats, f, indent=2)
            else:
                # Create new stats file
                with open(stats_filename, 'w') as f:
                    json.dump(self.summary_stats, f, indent=2)
        except Exception as e:
            print(f"Error saving stats: {e}")
        
        # Generate and save markdown report
        self.save_markdown_report(game_id, config)
        
        print(f"\nGame logs saved to {log_filename}")
        print(f"Stats saved to {stats_filename}")
        
        # Print summary
        self._print_summary()
    
    def _print_summary(self):
        """Print a summary of the game statistics"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n[{timestamp}] ===== GAME SUMMARY =====")
        print(f"Red wins: {self.summary_stats['red_wins']}")
        print(f"Blue wins: {self.summary_stats['blue_wins']}")
        print(f"Average game duration: {self.summary_stats['game_duration'] / max(self.summary_stats['red_wins'] + self.summary_stats['blue_wins'], 1):.2f} seconds")
        print(f"Average turns per game: {self.summary_stats['total_turns'] / max(self.summary_stats['red_wins'] + self.summary_stats['blue_wins'], 1):.2f}")
        
        # Team statistics
        print("\nRed Team:")
        red_guesses = max(self.summary_stats['red_team']['correct_guesses'] + self.summary_stats['red_team']['wrong_guesses'], 1)
        red_accuracy = self.summary_stats['red_team']['correct_guesses'] / red_guesses * 100
        print(f"  Guess accuracy: {red_accuracy:.2f}% ({self.summary_stats['red_team']['correct_guesses']}/{red_guesses})")
        
        print("\nBlue Team:")
        blue_guesses = max(self.summary_stats['blue_team']['correct_guesses'] + self.summary_stats['blue_team']['wrong_guesses'], 1)
        blue_accuracy = self.summary_stats['blue_team']['correct_guesses'] / blue_guesses * 100
        print(f"  Guess accuracy: {blue_accuracy:.2f}% ({self.summary_stats['blue_team']['correct_guesses']}/{blue_guesses})")
        print("=========================")

class AIGameManager:
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the AI Game Manager
        
        Args:
            config: Dict containing configuration options:
                - openai_api_key: OpenAI API key
                - red_spymaster_model: Model for red spymaster
                - red_operative_model: Model for red operative
                - blue_spymaster_model: Model for blue spymaster
                - blue_operative_model: Model for blue operative
                - log_dir: Directory for saving logs
                - num_games: Number of games to play
        """
        self.config = config
        self.engine = GameEngine(WORD_LIST)
        self.logger = GameLogger(config.get('log_dir', 'logs'))
        
        # Set up OpenAI client
        api_key =  os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key is required for AI vs AI game")
        
        self.client = openai.OpenAI(api_key=api_key)
        
        # Number of games to play
        self.num_games = config.get('num_games', 1)
    
    def setup_players(self) -> Dict[str, AIPlayer]:
        """Set up AI players for the game"""
        players = {
            "red_spymaster": AIPlayer(
                name="Red Spymaster",
                role=PlayerRole.SPYMASTER,
                team=Team.RED,
                model=self.config.get('red_spymaster_model', 'gpt-4o')
            ),
            "red_operative": AIPlayer(
                name="Red Operative",
                role=PlayerRole.OPERATIVE,
                team=Team.RED,
                model=self.config.get('red_operative_model', 'gpt-4o')
            ),
            "blue_spymaster": AIPlayer(
                name="Blue Spymaster",
                role=PlayerRole.SPYMASTER,
                team=Team.BLUE,
                model=self.config.get('blue_spymaster_model', 'gpt-4o')
            ),
            "blue_operative": AIPlayer(
                name="Blue Operative",
                role=PlayerRole.OPERATIVE,
                team=Team.BLUE,
                model=self.config.get('blue_operative_model', 'gpt-4o')
            )
        }
        
        return players
    
    def run_games(self):
        """Run the specified number of AI vs AI games"""
        for game_num in range(1, self.num_games + 1):
            print(f"\n\n========== STARTING GAME {game_num}/{self.num_games} ==========")
            self.play_game()
    
    def play_game(self):
        """Play a single AI vs AI game"""
        # Setup new game
        game_id = self.engine.create_game()
        if not game_id:
            print("Error creating game")
            return
        
        # Setup players
        players = self.setup_players()
        
        # Game stats
        start_time = time.time()
        game_start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n[{game_start_time}] Starting game {game_id}")
        
        # Log game start
        game_state = self.engine.get_game(game_id)
        if not game_state:
            print("Error retrieving game state")
            return
        
        self.logger.log_event("game_start", {
            "game_id": game_id,
            "start_time": game_start_time,
            "red_team": {
                "spymaster": players["red_spymaster"].name,
                "operative": players["red_operative"].name,
                "spymaster_model": players["red_spymaster"].model,
                "operative_model": players["red_operative"].model,
            },
            "blue_team": {
                "spymaster": players["blue_spymaster"].name,
                "operative": players["blue_operative"].name,
                "spymaster_model": players["blue_spymaster"].model,
                "operative_model": players["blue_operative"].model,
            }
        })
        
        # Log initial board state
        self._log_board_state(game_state, True)
        
        # Game stats
        turn_count = 0
        current_clue_index = -1
        
        # Main game loop
        while not game_state.winner:
            turn_count += 1
            current_team = game_state.current_team
            team_name = current_team.value
            
            # Get the current players
            if current_team == Team.RED:
                current_spymaster = players["red_spymaster"]
                current_operative = players["red_operative"]
            else:
                current_spymaster = players["blue_spymaster"]
                current_operative = players["blue_operative"]
            
            # Log board state for this turn
            self._log_board_state(game_state, True)
            
            # Get clue from spymaster
            clue_word, clue_number, target_words = self._get_ai_clue(current_spymaster, game_state)
            
            # Process the clue
            success = self.engine.process_clue(game_id, clue_word, clue_number, current_team)
            if not success:
                print("Error processing clue. Trying again.")
                continue
            
            # Log clue
            self.logger.log_event("clue", {
                "team": team_name,
                "player": current_spymaster.name,
                "word": clue_word,
                "number": clue_number,
                "model": current_spymaster.model,
                "target_words": target_words
            })
            
            # Add clue to summary stats and get index for tracking guesses
            current_clue_index = self.logger.log_clue(
                team_name, 
                clue_word, 
                clue_number, 
                current_spymaster.model,
                target_words
            )
            
            # Operatives guessing phase
            guesses_left = clue_number + 1  # Can guess one more than the clue number
            continue_guessing = True
            
            while continue_guessing and guesses_left > 0 and not game_state.winner:
                # Log board state for operative
                self._log_board_state(game_state, False)
                
                # Get AI operative's guess
                guess_word = self._get_ai_guess(current_operative, game_state, clue_word, clue_number)
                
                # Check if the operative decided to end the turn
                if guess_word == "_END_TURN_":
                    self.logger.log_event("turn_end", {
                        "team": team_name,
                        "reason": "Operative chose to end turn"
                    })
                    print(f"{current_operative.name} decides to END TURN")
                    self.engine.end_turn(game_id, current_team)
                    continue_guessing = False
                    continue
                
                # Process the guess
                result = self.engine.process_guess(game_id, guess_word, current_team)
                
                if not result or not result.get("success", False):
                    error_msg = result.get("error", "Unknown error") if result else "Invalid guess"
                    print(f"Error processing guess: {error_msg}")
                    continue
                
                # Get result details
                card_type = result.get("card_type", "unknown")
                correct_guess = card_type == team_name
                
                # Update stats
                if correct_guess:
                    self.logger.update_stats({
                        f"{team_name}_team": {"correct_guesses": 1, "wrong_guesses": 0}
                    })
                else:
                    self.logger.update_stats({
                        f"{team_name}_team": {"correct_guesses": 0, "wrong_guesses": 1}
                    })
                
                # Log the guess and result
                self.logger.log_event("guess", {
                    "team": team_name,
                    "player": current_operative.name,
                    "word": guess_word,
                    "result": f"{card_type.upper()} ({('Correct' if correct_guess else 'Wrong')})",
                    "model": current_operative.model
                })
                
                # Log guess in relation to the current clue
                self.logger.log_guess(
                    current_clue_index,
                    guess_word,
                    card_type,
                    correct_guess,
                    current_operative.model
                )
                
                # Check if the game is over
                game_state = self.engine.get_game(game_id)
                if game_state.winner:
                    winner = game_state.winner.value
                    end_time = time.time()
                    game_duration = end_time - start_time
                    
                    # Update stats
                    self.logger.update_stats({
                        f"{winner}_wins": 1,
                        "game_duration": game_duration,
                        "total_turns": turn_count
                    })
                    
                    # Log game end
                    self.logger.log_event("game_end", {
                        "winner": winner,
                        "duration": game_duration,
                        "total_turns": turn_count,
                        "start_time": game_start_time,
                        "end_time": end_time
                    })
                    
                    # Log final board state
                    self._log_board_state(game_state, True)
                    break
                
                # Check if turn ended
                if result.get("end_turn", True):
                    self.logger.log_event("turn_end", {
                        "team": team_name,
                        "reason": "Incorrect guess"
                    })
                    continue_guessing = False
                else:
                    guesses_left -= 1
                    if guesses_left <= 0:
                        self.logger.log_event("turn_end", {
                            "team": team_name,
                            "reason": "No more guesses left"
                        })
                        continue_guessing = False
                        self.engine.end_turn(game_id, current_team)
            
            # Refresh game state for next iteration
            game_state = self.engine.get_game(game_id)
        
        # Save logs and statistics
        self.logger.save_logs(game_id, self.config)
    
    def _log_board_state(self, game_state: GameState, for_spymaster: bool):
        """Log the current board state"""
        board_data = []
        for card in game_state.board:
            board_data.append({
                "word": card.word,
                "type": card.type.value,
                "revealed": card.revealed
            })
        
        self.logger.log_event("board_state", {
            "current_team": game_state.current_team.value,
            "red_remaining": game_state.red_remaining,
            "blue_remaining": game_state.blue_remaining,
            "board": board_data,
            "for_spymaster": for_spymaster
        })
    
    def _get_ai_clue(self, spymaster: AIPlayer, game_state: GameState) -> Tuple[str, int, List[str]]:
        """Get a clue from an AI spymaster"""
        board_state = game_state.get_spymaster_state(spymaster.team)
        
        # Prepare the message for the AI
        team_words = []
        opponent_words = []
        assassin_word = ""
        neutral_words = []
        
        for card in game_state.board:
            if not card.revealed:
                if card.type == spymaster.team:
                    team_words.append(card.word)
                elif card.type in [CardType.RED, CardType.BLUE]:
                    opponent_words.append(card.word)
                elif card.type == CardType.ASSASSIN:
                    assassin_word = card.word
                else:
                    neutral_words.append(card.word)
        
        # Information about game state
        team_remaining = len(team_words)
        opponent_remaining = len(opponent_words)
        
        prompt = f"""
You are the {spymaster.team.value} Spymaster in a game of Codenames. You need to give a one-word clue and a number.
The number indicates how many words on the board your clue relates to.

Your team's words to guess: {', '.join(team_words)}
Opponent's words (to avoid): {', '.join(opponent_words)}
Neutral words (to avoid): {', '.join(neutral_words)}
Assassin word (must avoid at all costs): {assassin_word}

Game situation:
- Your team has {team_remaining} words remaining
- Opponent has {opponent_remaining} words remaining

IMPORTANT STRATEGY:
- EFFICIENCY is crucial! Try to connect as many of your team's words as possible with a single clue.
- The faster your team finishes, the higher chance of winning, so aim for high-number clues.
- Prioritize clues that connect 3+ words when possible, even if the connection is more abstract.
- Avoid clues that might lead to the assassin or opponent's words.
- Be creative but clear - your operative must understand your thinking.

You MUST respond in EXACTLY this format:
CLUE: [your_clue_word]
NUMBER: [number_of_words]
TARGETS: [word1], [word2], etc.

The TARGETS must be words from your team's list above, and the NUMBER must match the count of TARGETS.
"""
        
        try:
            response = self.client.chat.completions.create(
                model=spymaster.model,
                messages=[
                    {"role": "system", "content": "You are a Codenames Spymaster AI focused on efficiency."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=100
            )
            
            # Parse the response
            response_text = response.choices[0].message.content.strip()
            
            # Extract clue, number, and targets
            clue_word = ""
            clue_number = 0
            target_words = []
            
            try:
                # More robust parsing with regular expressions
                import re
                
                # Extract clue
                clue_match = re.search(r"CLUE:\s*([\w\-]+)", response_text, re.IGNORECASE)
                if clue_match:
                    clue_word = clue_match.group(1).strip()
                
                # Extract number
                number_match = re.search(r"NUMBER:\s*(\d+)", response_text, re.IGNORECASE)
                if number_match:
                    clue_number = int(number_match.group(1))
                
                # Extract targets
                targets_match = re.search(r"TARGETS:\s*(.*?)(?:\n|$)", response_text, re.IGNORECASE)
                if targets_match:
                    targets_text = targets_match.group(1).strip()
                    # Split by commas and clean up each word
                    raw_targets = [word.strip() for word in targets_text.split(',')]
                    
                    # Filter for valid team words (case-insensitive matching)
                    team_words_lower = [word.lower() for word in team_words]
                    for target in raw_targets:
                        # Try to find a match in team words (not case sensitive)
                        for team_word in team_words:
                            if team_word.lower() == target.lower():
                                target_words.append(team_word)  # Use the original case from team_words
                                break
            except Exception as parse_error:
                print(f"Error parsing AI response: {parse_error}")
            
            # Fallback logic for when parsing fails
            if not clue_word:
                # Try to get the first word from the response
                words = response_text.split()
                if words:
                    clue_word = words[0].strip()
                
            # Make sure number matches targets if we have targets
            if target_words:
                if clue_number != len(target_words):
                    clue_number = len(target_words)
            # If we have a number but no targets, try to infer targets
            elif clue_number > 0:
                # Try to infer target words by similarity to the clue
                # This is a simplistic approach - in a real system, you'd use embeddings
                potential_targets = sorted(team_words, 
                                         key=lambda word: self._simple_word_similarity(clue_word, word),
                                         reverse=True)
                target_words = potential_targets[:min(clue_number, len(potential_targets))]
            # Default number if everything else fails
            elif clue_number <= 0:
                clue_number = 1
            
            # Log the decision
            spymaster.decisions.append({
                "type": "clue",
                "prompt": prompt,
                "response": response_text,
                "parsed": {
                    "word": clue_word,
                    "number": clue_number,
                    "targets": target_words
                }
            })
            
            print(f"Clue: {clue_word}, Number: {clue_number}, Targets: {target_words}")
            return clue_word, clue_number, target_words
                
        except Exception as e:
            print(f"Error getting AI clue: {e}")
            # Even in the fallback, try to provide plausible targets
            fallback_clue = random.choice(["fallback", "emergency", "backup"])
            if team_words:
                fallback_targets = random.sample(team_words, min(1, len(team_words)))
                return fallback_clue, len(fallback_targets), fallback_targets
            return fallback_clue, 1, []
    
    def _simple_word_similarity(self, word1: str, word2: str) -> float:
        """A basic similarity measure between words for fallback target inference"""
        word1, word2 = word1.lower(), word2.lower()
        
        # Check for exact match or substring
        if word1 == word2:
            return 1.0
        if word1 in word2 or word2 in word1:
            return 0.8
        
        # Count shared characters
        set1, set2 = set(word1), set(word2)
        shared = len(set1.intersection(set2))
        total = len(set1.union(set2))
        
        return shared / total if total > 0 else 0.0
    
    def _get_ai_guess(self, operative: AIPlayer, game_state: GameState, clue: str, number: int) -> str:
        """Get a guess from an AI operative or decide to end turn"""
        board_state = game_state.get_visible_state(operative.team)
        
        # Create a list of unrevealed words
        unrevealed_words = []
        revealed_words = []
        for card in game_state.board:
            if not card.revealed:
                unrevealed_words.append(card.word)
            elif card.revealed:
                revealed_words.append({"word": card.word, "type": card.type.value})
        
        # Get information about previous clues and guesses for context
        previous_clues = []
        for entry in self.logger.game_log:
            if entry["type"] == "clue":
                previous_clues.append({
                    "team": entry["details"]["team"],
                    "word": entry["details"]["word"],
                    "number": entry["details"]["number"]
                })
        
        # Calculate how many correct guesses we've made for current clue
        correct_guesses_this_turn = 0
        if self.logger.summary_stats["clues"] and len(self.logger.summary_stats["clues"]) > 0:
            current_clue = self.logger.summary_stats["clues"][-1]
            for guess in current_clue["guesses"]:
                if guess["is_correct"]:
                    correct_guesses_this_turn += 1
        
        # Prepare the message for the AI with strategic considerations
        prompt = f"""
You are the {operative.team.value} team Operative in a game of Codenames.

The Spymaster gave the clue: "{clue}" for {number} words.
So far, you've made {correct_guesses_this_turn} correct guesses for this clue.

The unrevealed words on the board are: {', '.join(unrevealed_words)}

Previous revealed words: {', '.join([f"{w['word']} ({w['type']})" for w in revealed_words])}

STRATEGIC DECISION REQUIRED:
1. You need to decide whether to GUESS a word or END your turn.
2. If you've already found all the words related to the current clue, it's often better to END your turn.
3. However, if you're very confident about another word, you might use the bonus guess.
4. If you decide to guess, pick exactly ONE word from the unrevealed list that best matches the clue.

First, analyze whether the words on the board relate to the clue "{clue}".
Then, make your decision:
- If you're confident about a word, respond with just that word.
- If you think you should end your turn, respond with just "END".

Your response should be ONLY the word you're guessing or "END" if you want to end your turn.
"""
        
        try:
            response = self.client.chat.completions.create(
                model=operative.model,
                messages=[
                    {"role": "system", "content": "You are a strategic Codenames Operative AI. Be concise."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=20
            )
            
            guess = response.choices[0].message.content.strip().lower()
            
            # Log the decision
            operative.decisions.append({
                "type": "guess",
                "prompt": prompt,
                "response": guess
            })
            
            # Check for END decision
            if guess == "end":
                # Signal to end turn
                return "_END_TURN_"
            
            # Check if the guess is in the list of unrevealed words
            valid_words = [card.word.lower() for card in game_state.board if not card.revealed]
            if guess in valid_words:
                return guess
            else:
                # Find the most similar word if the guess is invalid
                print(f"AI made an invalid guess: {guess}")
                
                # Find exact match for any word in the response
                for word in guess.split():
                    if word in valid_words:
                        return word
                
                # Default to random choice if no match found
                return random.choice(unrevealed_words)
                
        except Exception as e:
            print(f"Error getting AI guess: {e}")
            # Fallback to a random guess if API fails
            return random.choice(unrevealed_words)

def main():
    """Run AI vs AI games with the specified configuration"""
    # Check for OpenAI API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("OpenAI API key not found in environment. Please provide it.")
        api_key = input("Enter your OpenAI API key: ").strip()
        if not api_key:
            print("No API key provided. Exiting.")
            return
    
    # Default configuration
    config = {
        'openai_api_key': api_key,
        'red_spymaster_model': 'gpt-4o',
        'red_operative_model': 'gpt-4o',
        'blue_spymaster_model': 'gpt-4o',
        'blue_operative_model': 'gpt-4o',
        'log_dir': 'ai_game_logs',
        'num_games': 1
    }
    
    # Parse command line arguments if any
    import argparse
    parser = argparse.ArgumentParser(description='Run AI vs AI Codenames games')
    parser.add_argument('--num-games', type=int, default=1, help='Number of games to play')
    parser.add_argument('--red-spymaster', type=str, default='gpt-4o', help='Model for Red Spymaster')
    parser.add_argument('--red-operative', type=str, default='gpt-4o', help='Model for Red Operative')
    parser.add_argument('--blue-spymaster', type=str, default='gpt-4o', help='Model for Blue Spymaster')
    parser.add_argument('--blue-operative', type=str, default='gpt-4o', help='Model for Blue Operative')
    parser.add_argument('--log-dir', type=str, default='ai_game_logs', help='Directory for logs')
    
    args = parser.parse_args()
    
    # Update config with command line arguments
    config.update({
        'num_games': args.num_games,
        'red_spymaster_model': args.red_spymaster,
        'red_operative_model': args.red_operative,
        'blue_spymaster_model': args.blue_spymaster,
        'blue_operative_model': args.blue_operative,
        'log_dir': args.log_dir
    })
    
    print("\n===== CODENAMES AI VS AI =====")
    print(f"Running {config['num_games']} games with the following configuration:")
    print(f"Red Spymaster: {config['red_spymaster_model']}")
    print(f"Red Operative: {config['red_operative_model']}")
    print(f"Blue Spymaster: {config['blue_spymaster_model']}")
    print(f"Blue Operative: {config['blue_operative_model']}")
    print("=============================\n")
    
    # Run the games
    game_manager = AIGameManager(config)
    game_manager.run_games()

if __name__ == "__main__":
    main() 
