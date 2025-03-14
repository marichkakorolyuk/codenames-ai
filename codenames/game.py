"""
Core game logic for Codenames.
This module contains all the core game mechanics, data structures, and rules.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Union, Any
import uuid
import random


class CardType(Enum):
    """Enum representing different types of cards in the game"""
    RED = "red"
    BLUE = "blue"
    NEUTRAL = "neutral"
    ASSASSIN = "assassin"


@dataclass
class Card:
    """Represents a single card in the Codenames game"""
    word: str
    type: CardType
    revealed: bool = False


@dataclass
class Player:
    """Represents a player in the game"""
    id: str
    name: str
    team: CardType  # RED or BLUE
    role: str  # "spymaster" or "operative"
    is_ai: bool = False


@dataclass
class GameState:
    """Represents the current state of a Codenames game"""
    game_id: str
    board: List[Card]
    red_remaining: int
    blue_remaining: int
    current_team: CardType  # RED or BLUE
    winner: Optional[CardType] = None
    turn_count: int = 0
    clue_history: List[Tuple[CardType, str, int]] = field(default_factory=list)
    guess_history: List[Tuple[CardType, str, bool]] = field(default_factory=list)
    
    def get_visible_state(self, team: CardType) -> Dict:
        """Returns the game state as visible to a specific team's operatives."""
        visible_board = []
        for card in self.board:
            if card.revealed:
                visible_board.append({"word": card.word, "type": card.type.value, "revealed": True})
            else:
                visible_board.append({"word": card.word, "type": None, "revealed": False})
        
        return {
            "game_id": self.game_id,
            "board": visible_board,
            "red_remaining": self.red_remaining,
            "blue_remaining": self.blue_remaining,
            "current_team": self.current_team.value,
            "winner": self.winner.value if self.winner else None,
            "turn_count": self.turn_count,
            "clue_history": self.clue_history,
            "guess_history": self.guess_history
        }

    def get_spymaster_state(self, team: CardType) -> Dict:
        """Returns the game state as visible to a spymaster of a specific team."""
        spymaster_board = []
        for card in self.board:
            spymaster_board.append({
                "word": card.word, 
                "type": card.type.value, 
                "revealed": card.revealed
            })
        
        return {
            "game_id": self.game_id,
            "board": spymaster_board,
            "red_remaining": self.red_remaining,
            "blue_remaining": self.blue_remaining,
            "current_team": self.current_team.value,
            "winner": self.winner.value if self.winner else None,
            "turn_count": self.turn_count,
            "clue_history": self.clue_history,
            "guess_history": self.guess_history
        }

    def is_game_over(self) -> bool:
        """Check if the game is over."""
        return self.winner is not None

    def get_winner(self) -> Optional[str]:
        """Get the winner of the game, if any."""
        return self.winner.value if self.winner else None


class GameEngine:
    """Main game engine that handles game creation and state management"""
    
    def __init__(self, word_list: List[str]):
        """Initialize the game engine with a list of words to use."""
        self.games: Dict[str, GameState] = {}
        self.word_list = word_list
        
    def create_game(self, red_team_size: int = 2, blue_team_size: int = 2) -> str:
        """Create a new game with the specified team sizes."""
        game_id = str(uuid.uuid4())
        
        # Create board
        words = random.sample(self.word_list, 25)
        board = []
        
        # Determine first team
        first_team = random.choice([CardType.RED, CardType.BLUE])
        first_team_count = 9
        second_team_count = 8
        
        # Assign card types
        card_types = ([CardType.RED] * (first_team_count if first_team == CardType.RED else second_team_count) +
                      [CardType.BLUE] * (first_team_count if first_team == CardType.BLUE else second_team_count) +
                      [CardType.NEUTRAL] * 7 +
                      [CardType.ASSASSIN])
        random.shuffle(card_types)
        
        # Create board
        for i in range(25):
            board.append(Card(word=words[i], type=card_types[i]))
        
        # Create game state
        game_state = GameState(
            game_id=game_id,
            board=board,
            red_remaining=first_team_count if first_team == CardType.RED else second_team_count,
            blue_remaining=first_team_count if first_team == CardType.BLUE else second_team_count,
            current_team=first_team
        )
        
        self.games[game_id] = game_state
        return game_id
    
    def process_clue(self, game_id: str, clue_word: str, clue_number: int, team: CardType) -> bool:
        """Process a clue from a spymaster."""
        game = self.games.get(game_id)
        if not game:
            return False
            
        if game.current_team != team or game.winner:
            return False
        
        # Add to clue history
        game.clue_history.append((team, clue_word, clue_number))
        return True
    
    def process_guess(self, game_id: str, guess_word: str, team: CardType) -> Optional[Dict]:
        """Process a guess from an operative."""
        game = self.games.get(game_id)
        if not game:
            return None
            
        if game.current_team != team or game.winner:
            return None
        
        # Find the card
        guessed_card = None
        for card in game.board:
            if card.word.lower() == guess_word.lower() and not card.revealed:
                guessed_card = card
                break
                
        if not guessed_card:
            return {"success": False, "error": "Card not found or already revealed"}
        
        # Reveal the card
        guessed_card.revealed = True
        
        # Update counts and check winner
        card_type = guessed_card.type
        end_turn = True
        result = {
            "success": True, 
            "card_type": card_type.value, 
            "end_turn": True
        }
        
        if card_type == CardType.ASSASSIN:
            # Game over, current team loses
            game.winner = CardType.RED if team == CardType.BLUE else CardType.BLUE
            result["game_over"] = True
            result["winner"] = game.winner.value
            result["end_turn"] = True
            
        elif card_type == CardType.RED:
            game.red_remaining -= 1
            if game.red_remaining == 0:
                game.winner = CardType.RED
                result["game_over"] = True
                result["winner"] = CardType.RED.value
            # Only continue turn if correct team guessed their own card
            end_turn = team != CardType.RED
            result["end_turn"] = end_turn
            
        elif card_type == CardType.BLUE:
            game.blue_remaining -= 1
            if game.blue_remaining == 0:
                game.winner = CardType.BLUE
                result["game_over"] = True
                result["winner"] = CardType.BLUE.value
            # Only continue turn if correct team guessed their own card
            end_turn = team != CardType.BLUE
            result["end_turn"] = end_turn
        
        # Add to guess history - tuple of (team, word, correct_guess)
        correct_guess = (team == CardType.RED and card_type == CardType.RED) or \
                        (team == CardType.BLUE and card_type == CardType.BLUE)
        game.guess_history.append((team, guess_word, correct_guess))
        
        # End turn if needed
        if end_turn:
            game.turn_count += 1
            game.current_team = CardType.RED if game.current_team == CardType.BLUE else CardType.BLUE
        
        return result
    
    def end_turn(self, game_id: str, team: CardType) -> bool:
        """End the current team's turn."""
        game = self.games.get(game_id)
        if not game:
            return False
            
        if game.current_team != team or game.winner:
            return False
            
        game.turn_count += 1
        game.current_team = CardType.RED if game.current_team == CardType.BLUE else CardType.BLUE
        return True
    
    def get_game(self, game_id: str) -> Optional[GameState]:
        """Get a game by ID."""
        return self.games.get(game_id)
