import os
import pathlib
from openai import OpenAI
from pydantic import BaseModel
from typing import List, Optional, Dict
import random
import dotenv
from enum import Enum
import time
import weave

# Import necessary libraries

# Load environment variables from .env file
dotenv.load_dotenv()

# Check if the OpenAI API key is available in the environment
if not os.environ.get("OPENAI_API_KEY"):
    print("Warning: OPENAI_API_KEY environment variable not set.")
    print("Please ensure your .env file contains the OPENAI_API_KEY variable.")
    print("Example: OPENAI_API_KEY='your-api-key'")
    print("Exiting as the API key is required to run this script.")
    exit(1)

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

class DebateJudge(BaseModel):
    reasoning: str
    words_where_operatives_agree: List[str]
    words_where_operatives_disagree: List[str]

class ClueModel(BaseModel):
    clue: str
    selected_words: List[str]
    reasoning: str

class SimpleSpymasterAgent:
    """AI agent that plays as a Spymaster"""
    def __init__(self, team: CardType, name=None):
        """
        Initialize a new spymaster agent.
        
        Args:
            team: The team this agent belongs to
            name: Optional name for the agent
        """
        self.team = team
        self.name = name or f"Spymaster {team.value}"
        
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


        # Use OpenAI to generate the clue
        client = OpenAI()
        response = client.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "system", "content": prompt}
            ],
            response_format=ClueModel,
        )
        
        # Process response and return
                
        completion = response.choices[0].message.parsed
        return completion

class SimpleOperativeAgent:
    """AI agent that plays as a Operative"""
    def __init__(self, team: CardType, name = 'Smith'):
        self.name = str(name)
        self.team = team

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
        client = OpenAI()
        completion = client.chat.completions.create(
            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "user", "content": prompt},
            ],
            max_tokens=200
        )
        

        response = completion.choices[0].message
        return response.content

# Global variables for SimpleOperativeAgent to reference
unrevealed_words = []
revealed_words = []

# We don't need to track the last starting team anymore

import time
import weave
weave.init('codenames-ai')

@weave.op 
def play_codenames_game(team_red_size=2, team_blue_size=2, max_turns=20, seed=None, debate_rounds=2):
    """
    Play a complete game of Codenames using the existing agent implementations.
    
    Args:
        team_red_size: Number of operatives for the RED team
        team_blue_size: Number of operatives for the BLUE team
        max_turns: Maximum number of turns before ending the game
        seed: Random seed for reproducibility
        debate_rounds: Number of rounds of debate for each turn
        
    Returns:
        The final game state
    """
    # Start tracking game time
    start_time = time.time()
    
    # Initialize game variables
    
    # Initialize the game engine with the standard word list
    engine = GameEngine(WORD_LIST)
    
    # Create a new game
    game_id = engine.create_game(seed=seed)
    print(f"Created new game with ID: {game_id}")
    
    # Get the initial game state
    game_state = engine.get_game(game_id)
    print(game_state)
    
    # Initialize spymasters
    blue_spymaster = SimpleSpymasterAgent(CardType.BLUE)
    red_spymaster = SimpleSpymasterAgent(CardType.RED)
    
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
        
        # Generate a clue
        clue_model = current_spymaster.generate_clue(game_state)
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
            
        operatives = [SimpleOperativeAgent(current_team, f"Operative {i+1}") 
                     for i in range(team_size)]
        
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
        client = OpenAI()
        debate_model = client.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "system", "content": debate_judge_prompt}
            ],
            response_format=DebateJudge,
        ).choices[0].message.parsed
        
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
        
        selected_words = []
        # Combine agreed and disagreed words into a prioritized list
        all_words = filtered_agreed_words.copy()
        all_words.extend([word for word in filtered_disagreed_words if word not in all_words])
        
        if not all_words:
            print("No valid words were selected after debate. Skipping turn.")
            continue
        
        print(f"Prioritized words after debate: {all_words}")
        
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
    
    # Return both the game state and detailed outcome information
    return game_state, game_outcome

if __name__ == "__main__":
    # Define team sizes
    red_team_size = 2
    blue_team_size = 3
    
    # Call the game function with optional arguments for team sizes, max_turns and debate_rounds
    game_state, game_outcome = play_codenames_game(team_red_size=red_team_size, team_blue_size=blue_team_size, max_turns=20)
    
    # Print a summary of the game outcome
    print("\n===== GAME SUMMARY =====")
    print(f"Teams: RED={red_team_size} operatives, BLUE={blue_team_size} operatives")
    print(f"Turns played: {game_outcome['turns_played']}")
    if game_outcome['winner']:
        print(f"Winner: {game_outcome['winner']} team")
    print(f"Outcome: {game_outcome['win_reason']}")
    print(f"Total game time: {game_outcome['game_duration_seconds']:.2f} seconds")
