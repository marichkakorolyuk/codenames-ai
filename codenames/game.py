"""
Core game logic for Codenames.
This module contains all the core game mechanics, data structures, and rules.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Union, Any
import uuid
import random
import time


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
        
    def create_game(self, red_team_size: int = 2, blue_team_size: int = 2, seed = None) -> str:
        """Create a new game with the specified team sizes."""
        # Validate inputs
        assert red_team_size > 0, "Red team size must be positive"
        assert blue_team_size > 0, "Blue team size must be positive"
        
        if seed is None:
            # current timestamp
            seed = int(time.time())

        
        game_id = str(uuid.uuid4())[:8]
        
        # Create a local random number generator instead of using the global random state
        # This makes the method thread-safe and reproducible in parallel environments
        local_random = random.Random(seed)
        
        # Create board using local random generator
        assert len(self.word_list) >= 25, "Word list must contain at least 25 words"
        words = local_random.sample(self.word_list, 25)
        board = []
        
        # Determine first team
        first_team = local_random.choice([CardType.RED, CardType.BLUE])
        first_team_count = 9
        second_team_count = 8
        
        # Assign card types
        card_types = ([CardType.RED] * (first_team_count if first_team == CardType.RED else second_team_count) +
                      [CardType.BLUE] * (first_team_count if first_team == CardType.BLUE else second_team_count) +
                      [CardType.NEUTRAL] * 7 +
                      [CardType.ASSASSIN])
        local_random.shuffle(card_types)
        
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
        
        # Make sure game_id is unique
        assert game_id not in self.games, f"Game ID {game_id} already exists"
        self.games[game_id] = game_state
        return game_id

    def validate_clue(self, game: GameState, clue_word: str, selected_cards: List[str], team: CardType) -> Dict:
        """
        Validate a clue before processing it.
        
        Args:
            game: The current game state
            clue_word: The clue word provided by the spymaster
            selected_cards: List of card words the clue is intended for
            team: The team giving the clue
            
        Returns:
            Dictionary containing:
                - is_valid: Boolean indicating if the clue is valid
                - error: Error message if the clue is invalid, None otherwise
        """
        # Validate parameter types
        if not isinstance(game, GameState):
            return {
                'is_valid': False,
                'error': f"Expected GameState for game, got {type(game).__name__}"
            }
            
        if not isinstance(clue_word, str):
            return {
                'is_valid': False,
                'error': f"Expected string for clue_word, got {type(clue_word).__name__}"
            }
            
        if not isinstance(selected_cards, list):
            return {
                'is_valid': False,
                'error': f"Expected list for selected_cards, got {type(selected_cards).__name__}"
            }
            
        if not all(isinstance(card, str) for card in selected_cards):
            return {
                'is_valid': False,
                'error': "All selected cards must be strings"
            }
            
        if not isinstance(team, CardType):
            return {
                'is_valid': False,
                'error': f"Expected CardType for team, got {type(team).__name__}"
            }
        
        # Check if it's the team's turn
        if game.current_team != team:
            return {
                'is_valid': False,
                'error': f"It's not {team.value} team's turn"
            }
            
        # Check if the game is already won
        if game.winner:
            return {
                'is_valid': False, 
                'error': f"Game is already over. Winner: {game.winner.value}"
            }
            
        # Ensure clue word is a single word
        if not clue_word or len(clue_word.split()) > 1:
            return {
                'is_valid': False,
                'error': "Clue must be a single word"
            }
            
        # Check if the clue word appears on the board (not allowed by rules)
        board_words = [card.word.lower() for card in game.board]
        if clue_word.lower() in board_words:
            return {
                'is_valid': False,
                'error': f"Clue cannot be a word that appears on the board"
            }
            
        # Check if selected cards exist on the board
        for card_word in selected_cards:
            if card_word.lower() not in board_words:
                return {
                    'is_valid': False,
                    'error': f"Card '{card_word}' does not exist on the board"
                }
                
        # Check for duplicate cards in selection
        if len(selected_cards) != len(set(selected_cards)):
            return {
                'is_valid': False,
                'error': "Duplicate cards in selection"
            }
            
        # The clue is valid
        return {
            'is_valid': True,
            'error': None
        }
        
    def process_clue(self, game_id: str, clue_word: str, selected_cards: List[str], team: CardType) -> bool:
        """Process a clue from a spymaster."""
        game = self.games.get(game_id)
        assert game is not None
        
        validation_result = self.validate_clue(game, clue_word, selected_cards, team)
        
        if not validation_result['is_valid']:
            raise ValueError(validation_result['error'])
    
        if game.current_team != team or game.winner:
            return False
        
        # Add to clue history
        game.clue_history.append((team, clue_word, len(selected_cards), selected_cards))
        return True
    
    def process_guess(self, game_id: str, guess_word: str, team: CardType) -> Optional[Dict]:
        """Process a guess from an operative."""
        game = self.games.get(game_id)
        assert game is not None
            
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
        assert game is not None
            
        if game.current_team != team or game.winner:
            return False
            
        game.turn_count += 1
        game.current_team = CardType.RED if game.current_team == CardType.BLUE else CardType.BLUE
        return True
    
    def get_game(self, game_id: str) -> Optional[GameState]:
        """Get a game by ID."""
        return self.games.get(game_id)


def print_board(game_state: GameState, show_all: bool = False):
    """
    Display the game board in the terminal.
    
    Args:
        game_state: Current game state
        show_all: Whether to show all card types (spymaster view) or only revealed cards
    """
    print("\n" + "=" * 50)
    print(f"GAME: {game_state.game_id}")
    print(f"Turn: {game_state.turn_count + 1}, Current Team: {game_state.current_team.value.upper()}")
    print(f"RED remaining: {game_state.red_remaining}, BLUE remaining: {game_state.blue_remaining}")
    print("=" * 50)
    
    # Determine maximum word length for formatting
    max_length = max(len(card.word) for card in game_state.board)
    
    # Display the board as a 5x5 grid
    for i in range(0, 25, 5):
        row = game_state.board[i:i+5]
        
        # First, print the word row
        for j, card in enumerate(row):
            word = card.word.ljust(max_length + 2)
            print(f"{word}", end=" ")
        print()
        
        # Then, print the card type / status row
        for j, card in enumerate(row):
            if card.revealed or show_all:
                status = f"[{card.type.value.upper()}]".ljust(max_length + 2)
            else:
                status = f"[{j+i+1}]".ljust(max_length + 2)
            print(f"{status}", end=" ")
        print("\n")
    
    # Display recent history
    if game_state.clue_history:
        last_clue = game_state.clue_history[-1]
        # Make the team name more readable
        team_name = last_clue[0]
        if hasattr(team_name, 'value'):
            team_name = f"{team_name.value.upper()} Team"
        print(f"Last clue: '{last_clue[1]}' {last_clue[2]} (by {team_name})")
    
    if game_state.guess_history:
        print("Recent guesses:")
        for i in range(min(3, len(game_state.guess_history))):
            guess = game_state.guess_history[-(i+1)]
            
            # Make the team name more readable
            team = guess[0]
            if hasattr(team, 'value'):
                team_name = f"{team.value.upper()} Team"
            else:
                team_name = str(team)
            
            # Check the format of the card type entry
            if isinstance(guess[2], CardType):
                card_type = guess[2].value
            elif isinstance(guess[2], str):
                card_type = guess[2]
            elif isinstance(guess[2], bool):
                # If it's a boolean, it's probably a result flag, so get the card_type from the result dict
                # In this case, we'll just display the word's actual card type
                card = next((c for c in game_state.board if c.word == guess[1] and c.revealed), None)
                card_type = card.type.value if card else "unknown"
            else:
                card_type = str(guess[2])
                
            print(f"  - {team_name} guessed '{guess[1]}' ({card_type})")
    
    print("=" * 50 + "\n")
