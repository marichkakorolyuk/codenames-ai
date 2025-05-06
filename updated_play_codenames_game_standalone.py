import os
import pathlib
from openai import OpenAI
import os
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List, Optional, Dict
import random
import dotenv
from enum import Enum
import time
import weave
import sys
import datetime


# Import necessary libraries

# Load environment variables from .env file
dotenv.load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Set up logging to file
def setup_logging():
    # Create the game_logs directory if it doesn't exist
    logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "game_logs")
    os.makedirs(logs_dir, exist_ok=True)
    
    # Create a timestamp for the log file
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(logs_dir, f"game_log_{timestamp}.txt")
    
    # Create a class to duplicate stdout to both console and file
    class Logger(object):
        def __init__(self, filename):
            self.terminal = sys.stdout
            self.log = open(filename, "w")
            print(f"Logging game output to {filename}")
        
        def write(self, message):
            self.terminal.write(message)
            self.log.write(message)
            self.log.flush()
        
        def flush(self):
            self.terminal.flush()
            self.log.flush()
    
    # Redirect stdout to the Logger object
    sys.stdout = Logger(log_file)
    
    return log_file

# Initialize Weave for tracking experiments and game logs

weave.init('codenames-ai')

# Simplified logging function for weave
def log_event(event_name, **kwargs):
    # Just print the event - no actual weave logging for now
    print(f"Weave event: {event_name} - {kwargs}")


# Importing codenames game engine components
class CardType(Enum):
    RED = "red"
    BLUE = "blue"
    NEUTRAL = "neutral"
    ASSASSIN = "assassin"

class Card:
    def __init__(self, word, type, revealed=False):
        self.word = word
        self.type = type
        self.revealed = revealed

    def __repr__(self):
        return f"Card(word='{self.word}', type={self.type}, revealed={self.revealed})"

class GameState:
    def __init__(self, game_id, board, red_remaining, blue_remaining, current_team, winner=None, 
                 turn_count=0, clue_history=None, guess_history=None, random_seed=None):
        self.game_id = game_id
        self.board = board
        self.red_remaining = red_remaining
        self.blue_remaining = blue_remaining
        self.current_team = current_team
        self.winner = winner
        self.turn_count = turn_count
        self.clue_history = clue_history or []
        self.guess_history = guess_history or []
        self.random_seed = random_seed

    def __repr__(self):
        board_repr = ""
        for i in range(0, len(self.board), 5):
            row = self.board[i:i+5]
            words = [card.word.ljust(12) for card in row]
            types = [f"[{card.type.value.upper()}]".ljust(12) for card in row]
            board_repr += "".join(words) + "\n"
            board_repr += "".join(types) + "\n\n"

        clue_info = ""
        if self.clue_history:
            last_clue = self.clue_history[-1]
            clue_info = f"Last clue: '{last_clue[1]}' {last_clue[2]} (by {last_clue[0].value.upper()} Team)\n"

        return f"""
==================================================
GAME: {self.game_id} game_state.random_seed={self.random_seed}
Turn: {self.turn_count}, Current Team: {self.current_team.value.upper()}
RED remaining: {self.red_remaining}, BLUE remaining: {self.blue_remaining}
==================================================
{board_repr}
{clue_info}==================================================
"""

    def get_visible_state(self, team):
        """Return the game state with only revealed cards visible to the team"""
        visible_board = []
        for card in self.board:
            # If the card is revealed, show it as is
            if card.revealed:
                visible_board.append(card)
            else:
                # If the card is not revealed, hide its type
                visible_board.append(Card(card.word, CardType.NEUTRAL, False))
        
        return GameState(
            self.game_id,
            visible_board,
            self.red_remaining,
            self.blue_remaining,
            self.current_team,
            self.winner,
            self.turn_count,
            self.clue_history,
            self.guess_history,
            self.random_seed
        )

# Game Engine
class GameEngine:
    def __init__(self, word_list):
        self.word_list = word_list
        self.games = {}
    
    @weave.op()
    def create_game(self, seed=None):
        """Create a new Codenames game with randomized board"""
        if seed is None:
            seed = int(random.random() * 10000000000)
        random.seed(seed)
        
        # Generate a random game ID
        game_id = f"{random.randint(0, 16777215):06x}"
        
        # Select 25 random words for the board
        words = random.sample(self.word_list, 25)
        
        # Determine which team goes first - 50/50 chance
        first_team = CardType.RED if random.random() < 0.5 else CardType.BLUE
        
        # Assign card types - starting team always gets 9 cards
        card_types = []
        if first_team == CardType.RED:
            card_types = [CardType.RED] * 9 + [CardType.BLUE] * 8
        else:
            card_types = [CardType.RED] * 8 + [CardType.BLUE] * 9
        
        card_types += [CardType.NEUTRAL] * 7 + [CardType.ASSASSIN]
        random.shuffle(card_types)
        
        # Create the board
        board = [Card(word, card_type) for word, card_type in zip(words, card_types)]
        
        # Determine the remaining cards for each team
        red_count = sum(1 for card in board if card.type == CardType.RED)
        blue_count = sum(1 for card in board if card.type == CardType.BLUE)
        
        # Create initial game state
        game_state = GameState(
            game_id=game_id,
            board=board,
            red_remaining=red_count,
            blue_remaining=blue_count,
            current_team=first_team,
            random_seed=seed
        )
        
        # Store the game state
        self.games[game_id] = game_state
        
        return game_id
    
    def get_game(self, game_id):
        """Get the current state of a game"""
        return self.games.get(game_id)
    
    @weave.op()
    def process_clue(self, game_id, clue_word, num_words, team):
        """Process a spymaster's clue"""
        game_state = self.games.get(game_id)
        if not game_state:
            return False
        
        # Validate that it's the team's turn
        if game_state.current_team != team:
            return False
        
        # Record the clue
        game_state.clue_history.append((team, clue_word, num_words, []))
        
        return True
    
    @weave.op()
    def process_guess(self, game_id, word, team):
        """Process an operative's guess"""
        game_state = self.games.get(game_id)
        if not game_state:
            return {"success": False, "error": "Game not found"}
        
        # Validate that it's the team's turn
        if game_state.current_team != team:
            return {"success": False, "error": "Not your team's turn"}
        
        # Find the card
        card = None
        for c in game_state.board:
            if c.word.lower() == word.lower():
                card = c
                break
        
        if not card:
            return {"success": False, "error": f"Card '{word}' does not exist on the board"}
        
        if card.revealed:
            return {"success": False, "error": f"Card '{word}' has already been revealed"}
        
        # Mark the card as revealed
        card.revealed = True
        
        # Update the game state
        if card.type == CardType.RED:
            game_state.red_remaining -= 1
        elif card.type == CardType.BLUE:
            game_state.blue_remaining -= 1
        
        # Record the guess
        if game_state.clue_history:
            game_state.clue_history[-1][3].append(word)
        
        # Check for game over conditions
        if card.type == CardType.ASSASSIN:
            # The team that revealed the assassin loses
            game_state.winner = CardType.BLUE if team == CardType.RED else CardType.RED
        elif game_state.red_remaining == 0:
            game_state.winner = CardType.RED
        elif game_state.blue_remaining == 0:
            game_state.winner = CardType.BLUE
        
        # End turn if the guess was incorrect
        if card.type != team:
            game_state.current_team = CardType.BLUE if team == CardType.RED else CardType.RED
        
        return {"success": True, "card_type": card.type.value}
    
    def end_turn(self, game_id, team):
        """End the current team's turn"""
        game_state = self.games.get(game_id)
        if not game_state:
            return False
        
        # Validate that it's the team's turn
        if game_state.current_team != team:
            return False
        
        # Switch to the other team
        game_state.current_team = CardType.BLUE if team == CardType.RED else CardType.RED
        
        return True

# Word list - simplified for testing
WORD_LIST = [
    "africa", "agent", "air", "alien", "alps", "amazon", "ambulance", "america",
    "angel", "antarctica", "apple", "arm", "atlantis", "australia", "aztec",
    "back", "ball", "band", "bank", "bar", "bark", "bat", "battery", "beach",
    "bear", "beat", "bed", "beijing", "bell", "belt", "berlin", "bermuda",
    "berry", "bill", "block", "board", "bolt", "bomb", "bond", "boom", "boot",
    "bottle", "bow", "box", "bridge", "brush", "buck", "buffalo", "bug",
    "bugle", "button", "calf", "canada", "cap", "capital", "car", "card",
    "carrot", "casino", "cast", "cat", "cell", "centaur", "center", "chair",
    "change", "charge", "check", "chest", "chick", "china", "chocolate",
    "church", "circle", "cliff", "cloak", "club", "code", "cold", "comic",
    "compound", "concert", "conductor", "contract", "cook", "copper", "cotton",
    "court", "cover", "crane", "crash", "cricket", "cross", "crown", "cycle",
    "czech", "dance", "date", "day", "death", "deck", "degree", "diamond",
    "dice", "dinosaur", "disease", "doctor", "dog", "draft", "dragon", "dress",
    "drill", "drop", "duck", "dwarf", "eagle", "egypt", "embassy", "engine",
    "england", "europe", "eye", "face", "fair", "fall", "fan", "fence", "field",
    "fighter", "figure", "file", "film", "fire", "fish", "flute", "fly", "foot",
    "force", "forest", "fork", "france", "game", "gas", "genius", "germany",
    "ghost", "giant", "glass", "glove", "gold", "grace", "grass", "greece",
    "green", "ground", "ham", "hand", "hawk", "head", "heart", "helicopter",
    "himalayas", "hole", "hollywood", "honey", "hood", "hook", "horn", "horse",
    "horseshoe", "hospital", "hotel", "ice", "ice cream", "india", "iron",
    "ivory", "jack", "jam", "jet", "jupiter", "kangaroo", "ketchup", "key",
    "kid", "king", "kiwi", "knife", "knight", "lab", "lap", "laser", "lawyer",
    "lead", "lemon", "leprechaun", "life", "light", "limousine", "line", "link",
    "lion", "litter", "loch ness", "lock", "log", "london", "luck", "mail",
    "mammoth", "maple", "marble", "march", "mass", "match", "mercury", "mexico",
    "microscope", "millionaire", "mine", "mint", "missile", "model", "mole",
    "moon", "moscow", "mount", "mouse", "mouth", "mug", "nail", "needle", "net",
    "new york", "night", "ninja", "note", "novel", "nurse", "nut", "octopus",
    "oil", "olive", "olympus", "opera", "orange", "organ", "palm", "pan",
    "pants", "paper", "parachute", "park", "part", "pass", "paste", "penguin",
    "phoenix", "piano", "pie", "pilot", "pin", "pipe", "pirate", "pistol",
    "pit", "pitch", "plane", "plastic", "plate", "platypus", "play", "plot",
    "point", "poison", "pole", "police", "pool", "port", "post", "pound",
    "press", "princess", "pumpkin", "pupil", "pyramid", "queen", "rabbit",
    "racket", "ray", "revolution", "ring", "robin", "robot", "rock", "rome",
    "root", "rose", "roulette", "round", "row", "ruler", "satellite", "saturn",
    "scale", "school", "scientist", "scorpion", "screen", "scuba diver", "seal",
    "server", "shadow", "shakespeare", "shark", "ship", "shoe", "shop", "shot",
    "sink", "skyscraper", "slip", "slug", "smuggler", "snow", "snowman",
    "sock", "soldier", "soul", "sound", "space", "spell", "spider", "spike",
    "spine", "spot", "spring", "spy", "square", "stadium", "staff", "star",
    "state", "stick", "stock", "straw", "stream", "strike", "string", "sub",
    "suit", "superhero", "swing", "switch", "table", "tablet", "tag", "tail",
    "tap", "teacher", "telescope", "temple", "theater", "thief", "thumb",
    "tick", "tie", "time", "tokyo", "tooth", "torch", "tower", "track", "train",
    "triangle", "trip", "trunk", "tube", "turkey", "undertaker", "unicorn",
    "vacuum", "van", "vet", "wake", "wall", "war", "washer", "washington",
    "watch", "water", "wave", "web", "well", "whale", "whip", "wind", "witch",
    "worm", "yard"
]

# AI Agents

class DebateJudgeResult(BaseModel):
    reasoning: str
    words_where_operatives_agree: List[str]
    words_where_operatives_disagree: List[str]

class ClueModel(BaseModel):
    clue: str
    selected_words: List[str]
    reasoning: str

class SimpleSpymasterAgent:
    """AI agent that plays as a Spymaster"""
    def __init__(self, team: CardType, name=None, model="anthropic/claude-3-haiku"):
        """
        Initialize a new spymaster agent.
        
        Args:
            team: The team this agent belongs to
            name: Optional name for the agent
            model: The AI model to use for this agent
        """
        self.team = team
        self.name = name or f"Spymaster"
        self.model = model
        
    @weave.op()
    def generate_clue(self, game_state: GameState) -> ClueModel:
        """
        Generate a clue for the operatives.
        
        Args:
            game_state: The current game state
            max_completion_tokens: Maximum number of tokens for the response
            
        Returns:
            A ClueModel with the clue word, selected words, and reasoning
        """
        # Get words for my team
        my_words = []
        for card in game_state.board:
            if not card.revealed and card.type == self.team:
                my_words.append(card.word)
        # Define all variables needed for the prompt
        opponent_team = CardType.RED if self.team == CardType.BLUE else CardType.BLUE
        team_words = my_words  # Words for this team
        opponent_words = []    # Words for opposing team
        neutral_words = []     # Neutral words
        assassin_word = ""     # The assassin word

        for card in game_state.board:
            if not card.revealed:
                if card.type == opponent_team:
                    opponent_words.append(card.word)
                elif card.type == CardType.NEUTRAL:
                    neutral_words.append(card.word)
                elif card.type == CardType.ASSASSIN:
                    assassin_word = card.word

        # Count remaining words
        team_remaining = len(team_words)
        opponent_remaining = len(opponent_words)

        # Get round number from game state
        round_number = game_state.turn_count + 1

        # Build team history from previous clues and guesses
        team_history = ""
        if game_state.clue_history and game_state.guess_history:
            history_entries = []
            for i, (clue, guesses) in enumerate(zip(game_state.clue_history, game_state.guess_history)):
                if clue.get('team') == self.team.value:
                    guess_words = ", ".join([g.get('word', '') for g in guesses if g.get('team') == self.team.value])
                    if guess_words:
                        history_entries.append(f"Round {i+1}: Clue '{clue.get('word')}' {clue.get('number')} → Selected: {guess_words}")
            team_history = "; ".join(history_entries)

        # Load the prompt from file
        prompt_file = pathlib.Path("prompts/spymaster_prompt.txt")
        with open(prompt_file, "r") as f:
            prompt_template = f.read()
        
        # Format the prompt with variables
        prompt = prompt_template.format(
            team=self.team.value,
            round_number=round_number,
            team_words=', '.join(team_words),
            opponent_words=', '.join(opponent_words),
            neutral_words=', '.join(neutral_words),
            assassin_word=assassin_word,
            team_remaining=team_remaining,
            opponent_remaining=opponent_remaining,
            team_history=team_history
        )


        # Use OpenRouter to generate the clue
        # Use OpenRouter with direct API key
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY
        )
        # Format prompt with strict instructions for JSON output
        enhanced_prompt = prompt + "\n\nYou MUST respond ONLY with a valid JSON object and nothing else. No explanations before or after the JSON. The JSON structure must be: {\"reasoning\": \"your reasoning\", \"clue\": \"your_clue_word\", \"selected_words\": [\"word1\", \"word2\"]}"
        
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": enhanced_prompt}
            ],
            extra_headers={
                "HTTP-Referer": "https://github.com/mariiakoroliuk/codenames-ai",
                "X-Title": "Codenames AI"
            },
            response_format={"type": "json_object"}
        )
        
        # Process response and manually parse JSON
        response_text = response.choices[0].message.content
        
        try:
            import json
            import re
            
            # Try to extract JSON using regex if needed
            json_match = re.search(r'(\{.*?\})', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                parsed_response = json.loads(json_str)
            else:
                parsed_response = json.loads(response_text)
                
            # Log the full reasoning from the spymaster
            full_reasoning = parsed_response.get("reasoning", "No reasoning provided")
            print("\n=== SPYMASTER REASONING ===\n")
            print(full_reasoning)
            print("\n=== END SPYMASTER REASONING ===\n")
            
            # Convert to ClueModel object
            completion = ClueModel(
                clue=parsed_response.get("clue", ""),
                selected_words=parsed_response.get("selected_words", []),
                reasoning=parsed_response.get("reasoning", "")
            )
            return completion
        except Exception as e:
            print(f"Error parsing response: {e}")
            print(f"Raw response: {response_text}")
            # Extract words from board for fallback
            team_words = [card.word for card in game_state.board if card.type == self.team and not card.revealed]
            # Fallback with reasonable values
            return ClueModel(clue="backup", 
                           selected_words=team_words[:2] if team_words else ["fallback"], 
                           reasoning="Error in parsing response")

class SimpleOperativeAgent:
    """AI agent that plays as a Operative"""
    def __init__(self, team: CardType, name = 'Smith', model="anthropic/claude-3-haiku", max_tokens=800):
        self.name = str(name)
        self.team = team
        self.model = model
        self.max_tokens = max_tokens

    @weave.op()
    def generate(self, clue_word, clue_n_words, debate_history):
        # Access the global variables
        global unrevealed_words, revealed_words
        
        # Load the prompt from file
        prompt_file = pathlib.Path("prompts/operative_prompt.txt")
        with open(prompt_file, "r") as f:
            prompt_template = f.read()
        
        # Format the prompt with variables
        prompt = prompt_template.format(
            name=self.name,
            team=self.team.value,
            clue_word=clue_word,
            clue_n_words=clue_n_words,
            debate_history=debate_history,
            unrevealed_words=', '.join(unrevealed_words),
            revealed_words=', '.join(revealed_words)
        )
        # Use OpenRouter with direct API key
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY
        )
        completion = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "user", "content": prompt},
            ],
            extra_headers={
                "HTTP-Referer": "https://github.com/mariiakoroliuk/codenames-ai",
                "X-Title": "Codenames AI"
            },
            max_tokens=self.max_tokens
        )
        

        response = completion.choices[0].message
        return response.content

class DebateJudge:
    """AI agent that judges debates between operatives"""
    def __init__(self, model="anthropic/claude-3-haiku", max_tokens=1200):
        self.model = model
        self.max_tokens = max_tokens

    @weave.op()
    def generate(self, debate_history, clue_word, clue_n_words, round_number=1, current_team="unknown"):
        # Load the prompt from file
        prompt_file = pathlib.Path("prompts/judge_prompt.txt")
        with open(prompt_file, "r") as f:
            prompt_template = f.read()
        
        # Format the prompt with variables
        debate_judge_prompt = prompt_template.format(
            current_team=current_team,
            round_number=round_number,
            clue_word=clue_word,
            clue_n_words=clue_n_words,
            debate_history=debate_history
        )
        
        print("Using DebateJudge to resolve the debate...")
        print(f"Using model: {self.model}")
        
        # Use OpenRouter with direct API key
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY
        )
        
        # Format prompt with strict instructions for JSON output
        enhanced_prompt = debate_judge_prompt + "\n\nYou MUST respond ONLY with a valid JSON object and nothing else. No explanations before or after the JSON. The JSON structure must be: {\"reasoning\": \"your reasoning\", \"words_where_operatives_agree\": [\"word1\", \"word2\"], \"words_where_operatives_disagree\": [\"word3\", \"word4\"]}"
        
        # Make API call with the model specified during initialization
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": enhanced_prompt}
            ],
            extra_headers={
                "HTTP-Referer": "https://github.com/mariiakoroliuk/codenames-ai",
                "X-Title": "Codenames AI"
            },
            response_format={"type": "json_object"},
            max_tokens=self.max_tokens
        )
        
        # Extract reasoning from the response
        response_text = response.choices[0].message.content
        
        try:
            import json
            import re
            
            # Try to extract JSON using regex if needed
            json_match = re.search(r'(\{.*?\})', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                parsed_response = json.loads(json_str)
            else:
                parsed_response = json.loads(response_text)
            
            # Log the full reasoning from the judge
            full_reasoning = parsed_response.get("reasoning", "No reasoning provided")
            print("\n=== JUDGE REASONING ===\n")
            print(full_reasoning)
            print("\n=== END JUDGE REASONING ===\n")
            
            # Create and return the result
            return DebateJudgeResult(
                reasoning=parsed_response.get("reasoning", ""),
                words_where_operatives_agree=parsed_response.get("words_where_operatives_agree", []),
                words_where_operatives_disagree=parsed_response.get("words_where_operatives_disagree", [])
            )
            
        except Exception as e:
            print(f"Error parsing judge response: {e}")
            print(f"Raw response: {response_text}")
            # Return empty result as fallback
            return DebateJudgeResult(
                reasoning="Error parsing response",
                words_where_operatives_agree=[],
                words_where_operatives_disagree=[]
            )

# Global variables for SimpleOperativeAgent to reference
unrevealed_words = []
revealed_words = []

# We don't need to track the last starting team anymore

import time

@weave.op 
def play_codenames_game(
    team_red_size,
    team_blue_size,
    max_turns ,
    seed ,
    debate_rounds, 
    red_model, 
    blue_model, 
    judge_model,
    red_models,
    blue_models,
    ):
    """
    Play a complete game of Codenames using the existing agent implementations.
    
    Args:
        team_red_size: Number of operatives for the RED team
        team_blue_size: Number of operatives for the BLUE team
        max_turns: Maximum number of turns before ending the game
        seed: Random seed for reproducibility
        debate_rounds: Number of rounds of debate for each turn
        red_model: The model to use for RED team agents
        blue_model: The model to use for BLUE team agents
        judge_model: The model to use for the debate judge
        
    Returns:
        The final game state
    """
    
    # Backward compatibility: If no models are provided, use the default model for each team
    # The +1 is for the spymaster
    if red_models is None:
        red_models = [red_model] * (team_red_size)
    else:
        team_red_size = len(red_models)
    if blue_models is None:
        blue_models = [blue_model] * (team_blue_size)
    else:
        team_blue_size = len(blue_models)
    
    # Start tracking game time
    start_time = time.time()
    
    # Initialize game variables
    
    # Initialize the game engine with the standard word list
    engine = GameEngine(WORD_LIST)
    
    # Create a new game
    game_id = engine.create_game(seed=seed)
    # Simple logging instead of weave logging
    log_event("game_created", game_id=game_id, seed=seed)
    print(f"Created new game with ID: {game_id}")
    
    # Get the initial game state
    game_state = engine.get_game(game_id)
    # Simple logging for game start
    log_event("game_started", 
             starting_team=game_state.current_team.value,
             red_cards=game_state.red_remaining,
             blue_cards=game_state.blue_remaining)
    print(game_state)
    
    # Initialize spymasters with team-specific models
    blue_spymaster = SimpleSpymasterAgent(CardType.BLUE, model=blue_models[0])
    red_spymaster = SimpleSpymasterAgent(CardType.RED, model=red_models[0])
    print(f"Created RED spymaster using {red_models[0]}")
    print(f"Created BLUE spymaster using {blue_models[0]}")
    
    # Helper function to get the current spymaster
    def get_current_spymaster_agent(game_state):
        return blue_spymaster if game_state.current_team == CardType.BLUE else red_spymaster
    
    turn_count = 0
    
    # Game loop - checking for winner instead of game_over
    while game_state.winner is None and turn_count < max_turns:
        turn_count += 1
        print(f"\n=== TURN {turn_count} ===")
        
        # Get current team
        current_team = game_state.current_team
        print(f"Current team: {current_team.value.upper()}")
        
        # Get current spymaster
        current_spymaster = get_current_spymaster_agent(game_state)
        
        # Log which model is being used for the spymaster
        current_model = red_model if current_team == CardType.RED else blue_model
        print(f"Created {current_team.value.upper()} spymaster using {current_model}")
        
        # Generate a clue
        clue_model = current_spymaster.generate_clue(game_state)
        # Simple logging for clue generation
        log_event("clue_generated", 
                 turn=turn_count, 
                 team=current_team.value, 
                 clue_word=clue_model.clue)
        
        # Log the target words the spymaster had in mind
        print(f"Spymaster's target words: {clue_model.selected_words}")
        clue_word = clue_model.clue
        clue_n_words = len(clue_model.selected_words)
        
        print(f"Spymaster gives clue: '{clue_word}' {clue_n_words}")
        
        # Get the current team's view of the board
        current_team_state = game_state.get_visible_state(current_team)
        
        # Create lists of unrevealed and revealed words from the current board state
        # These need to be global variables since SimpleOperativeAgent references them directly
        global unrevealed_words, revealed_words
        
        unrevealed_words = []
        revealed_words = []
        
        for card in current_team_state.board:
            if card.revealed:
                revealed_words.append(card.word.lower())
            else:
                unrevealed_words.append(card.word.lower())
        
        print(f"Unrevealed words: {unrevealed_words}")
        print(f"Revealed words: {revealed_words}")
        
        # Initialize operatives for the current team with available words using the appropriate team size
        if current_team == CardType.RED:
            team_size = team_red_size
        else:  # BLUE team
            team_size = team_blue_size
            
        # Create operatives with the appropriate model for the current team
        if current_team == CardType.RED:
            operatives = [SimpleOperativeAgent(current_team, f"Operative {i}", model=red_models[i])
                          for i in range(1, team_size)]
        else:  # BLUE team
            operatives = [SimpleOperativeAgent(current_team, f"Operative {i}", model=blue_models[i])
                          for i in range(1, team_size)]
        
        # Print available words for debugging
        print(f"Available words for operatives: {unrevealed_words}")
        
        # Run the debate
        debate_history = []
        
        for turn_i in range(debate_rounds):
            print(f'Debate round {turn_i+1}:')
            
            this_turn_reasoning = {}
            for op in operatives:
                try:
                    # SimpleOperativeAgent is designed to use global variables
                    # We've already defined them at the beginning of the function

                    reasoning = op.generate(clue_word, clue_n_words, str(debate_history))
                    this_turn_reasoning[op.name] = reasoning
                    
                    print(f'Operative {op.name} says:')
                    print(reasoning)
                except KeyboardInterrupt:
                    print("KeyboardInterrupt received. Stopping debate.")
                    break
            
            debate_history.append(this_turn_reasoning)
        
        # Define variables needed for the debate judge prompt
        round_number = game_state.turn_count + 1
        
        # Load the prompt from file
        prompt_file = pathlib.Path("prompts/judge_prompt.txt")
        with open(prompt_file, "r") as f:
            prompt_template = f.read()
        
        # Format the prompt with variables
        debate_judge_prompt = prompt_template.format(
            current_team=current_team.value,
            round_number=round_number,
            clue_word=clue_word,
            clue_n_words=clue_n_words,
            debate_history=debate_history
        )
        
        print("Using DebateJudge to resolve the debate...")
        print(f"Using model: {judge_model}")
        # Create a debate judge with the specified model
        judge = DebateJudge(model=judge_model)
        
        # Use the judge to analyze the debate and get results
        debate_model = judge.generate(
            debate_history=debate_history,
            clue_word=clue_word,
            clue_n_words=clue_n_words,
            round_number=round_number,
            current_team=current_team.value
        )
        
        # Simple logging for debate outcome
        log_event("debate_completed", 
                 turn=turn_count, 
                 team=current_team.value, 
                 agreed_words_count=len(debate_model.words_where_operatives_agree))
        
        print("Agreed upon words:", debate_model.words_where_operatives_agree)
        print("Disagreed upon words:", debate_model.words_where_operatives_disagree)
        
        # Filter the debate words to only include words actually on the board
        # Make sure we strictly compare with the original board words
        filtered_agreed_words = []
        for word in debate_model.words_where_operatives_agree:
            word_lower = word.lower()
            if word_lower in unrevealed_words:
                filtered_agreed_words.append(word_lower)
            else:
                print(f"Warning: '{word}' is not on the board or already revealed")
                
        filtered_disagreed_words = []
        for word in debate_model.words_where_operatives_disagree:
            word_lower = word.lower()
            if word_lower in unrevealed_words:
                filtered_disagreed_words.append(word_lower)
            else:
                print(f"Warning: '{word}' is not on the board or already revealed")
        
        print("Filtered agreed words (on board):", filtered_agreed_words)
        print("Filtered disagreed words (on board):", filtered_disagreed_words)
        
        # Only use agreed words for guessing, not disagreed words
        all_words = filtered_agreed_words.copy()
        
        # If there are no agreed words, only then consider disagreed words
        if not all_words:
            all_words = filtered_disagreed_words.copy()
        
        if not all_words:
            print("No valid words were selected after debate. Skipping turn.")
            continue
        
        print(f"Prioritized words after debate: {all_words}")
        # Log whether we're using agreed words only or had to fall back to disagreed words
        if filtered_agreed_words:
            print("Using only words where operatives agreed")
        else:
            print("No agreed words found, falling back to words where operatives disagreed")
        
        # Process the clue to start the guessing phase
        try:
            # Important: Pass a list of selected_cards not an integer for clue_n_words
            # This will start the clue phase without any guesses yet
            selected_cards = []  # Empty list to start with
            clue_result = engine.process_clue(game_id, clue_word, selected_cards, current_team)
            print(f"Clue processed: {clue_result}")
            
            # Guessing phase - process one word at a time
            guesses_left = clue_n_words + 1  # Additional guess as per Codenames rules
            continue_guessing = True
            guessed_words = []
            
            while continue_guessing and guesses_left > 0 and len(all_words) > 0:
                # Get the next word to guess
                guess_word = all_words.pop(0)
                print(f"\nGuessing word: {guess_word}")
                
                # Process the guess
                guess_result = engine.process_guess(game_id, guess_word, current_team)
                
                if not guess_result or not guess_result.get("success", False):
                    error_msg = guess_result.get("error", "Unknown error") if guess_result else "Invalid guess"
                    print(f"Error processing guess: {error_msg}")
                    continue
                
                # Get result details
                card_type = guess_result.get("card_type", "unknown")
                correct_guess = card_type == current_team.value
                guessed_words.append(guess_word)
                
                # Simple logging for guess
                log_event("guess_made", 
                         turn=turn_count, 
                         team=current_team.value, 
                         word=guess_word, 
                         correct=correct_guess)
                
                print(f"Guess result: {card_type.upper()} card revealed")
                
                # Update game state
                game_state = engine.get_game(game_id)
                
                # Check if game is over
                if game_state.winner is not None:
                    break
                
                # Determine if we should continue guessing
                if not correct_guess:
                    print("Incorrect guess - ending turn")
                    continue_guessing = False
                else:
                    print("Correct guess - can continue guessing")
                    guesses_left -= 1
                    print(f"Guesses left: {guesses_left}")
                    
                    # If we've used all our guesses but still have one bonus
                    if guesses_left == 1 and clue_n_words > 0:
                        print("Used all clue-based guesses, now using bonus guess")
            
            print(f"Turn complete. Words guessed this turn: {guessed_words}")
            
            # Update game state
            game_state = engine.get_game(game_id)
            
            # Simple logging for turn completion
            log_event("turn_completed", 
                     turn=turn_count, 
                     team=current_team.value, 
                     red_remaining=game_state.red_remaining, 
                     blue_remaining=game_state.blue_remaining)
            
            # Switch teams for the next turn if game is not over
            if game_state.winner is None:
                # Switch from RED to BLUE or BLUE to RED
                game_state.current_team = CardType.BLUE if current_team == CardType.RED else CardType.RED
                # Update turn count in game state
                game_state.turn_count = turn_count
            
            print(game_state)
            
        except ValueError as e:
            print(f"Error processing clue: {e}")
    
    # Track win reason and prepare detailed outcome information
    end_time = time.time()
    game_duration = end_time - start_time
    
    # Log model information
    print(f"\n===== MODEL INFORMATION =====")
    print(f"RED Team Model: {red_model}")
    print(f"BLUE Team Model: {blue_model}")
    print(f"Judge Model: {judge_model}")
    
    
    game_outcome = {
        "turns_played": turn_count,
        "winner": None,
        "win_reason": None,
        "game_duration_seconds": game_duration
    }
    
    # Game over
    if game_state.winner is not None:
        winner_team = "RED" if game_state.winner == CardType.RED else "BLUE"
        
        # Determine why the game ended
        assassin_revealed = any(card.type == CardType.ASSASSIN and card.revealed for card in game_state.board)
        
        if assassin_revealed:
            win_reason = f"{winner_team} team won because the opposing team revealed the ASSASSIN card"
        else:
            win_reason = f"{winner_team} team won by uncovering all their cards"
        
        game_outcome["winner"] = winner_team
        game_outcome["win_reason"] = win_reason
        
        print(f"\nGame over! {winner_team} team wins!")
        print(f"Reason: {win_reason}")
        print(f"Game completed in {turn_count} turns")
        print(f"Game duration: {game_duration:.2f} seconds")
    else:
        game_outcome["win_reason"] = "Game ended due to maximum turn limit"
        print("\nGame ended due to maximum turn limit")
        print(f"Game played for maximum {turn_count} turns")
        print(f"Game duration: {game_duration:.2f} seconds")
    
    # Simple logging for game end
    log_event("game_ended", outcome=game_outcome)
    
    # Return both the game state and detailed outcome information
    return game_state, game_outcome

if __name__ == "__main__":
    # Set up logging to file
    log_file = setup_logging()
    
    
    # Define models for each team - can be customized
    # Available models include:
    # - "anthropic/claude-3-opus" (powerful Claude model)
    # - "anthropic/claude-3-sonnet" (mid-tier Claude model)
    # - "anthropic/claude-3-haiku" (faster, smaller Claude model)
    # - "openai/gpt-4-turbo" (OpenAI's GPT-4 model)
    # - "google/gemini-1.5-pro" (Google's Gemini model)
    # - "meta-llama/llama-3-70b-instruct" (Meta's Llama model)

    try:
        # Call the game function with optional arguments for team sizes, max_turns and debate_rounds
        game_state, game_outcome = play_codenames_game(
            team_red_size=4, 
            team_blue_size=4, 
            max_turns=20, 
            seed=None, 
            debate_rounds=2, 
            red_model="deepseek/deepseek-prover-v2:free",
            blue_model="deepseek/deepseek-prover-v2:free",
            judge_model="openai/gpt-4.1",
            red_models=["deepseek/deepseek-prover-v2:free"] * 4,
            blue_models=["deepseek/deepseek-prover-v2:free"] * 4
        )
        

        # Print a summary of the game outcome
        print("\n===== GAME SUMMARY =====")
        print(f"Teams: RED={team_red_size} operatives, BLUE={team_blue_size} operatives")
        print(f"Models used: RED={red_model}, BLUE={blue_model}, JUDGE={judge_model}")
        print(f"Turns played: {game_outcome['turns_played']}")
        if game_outcome['winner']:
            print(f"Winner: {game_outcome['winner']} team")
        print(f"Outcome: {game_outcome['win_reason']}")
        print(f"Total game time: {game_outcome['game_duration_seconds']:.2f} seconds")
    except KeyboardInterrupt:
        print("\nGame interrupted by user.")
    except Exception as e:
        print(f"\nError occurred: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Reset stdout
        sys.stdout = sys.__stdout__
        print(f"Game log saved to {log_file}")
