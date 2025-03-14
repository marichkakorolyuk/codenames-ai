#!/usr/bin/env python3
"""
Codenames Debates Example

This file demonstrates how to use the debate functionality in the Codenames AI project.
It shows:

1. How to create AI agents for both teams
2. How to set up and use the DebateManager
3. How to run AI vs AI games with proper debate handling
4. How teams make decisions collaboratively through debate

This example requires an OpenAI API key to work properly.
"""

import os
import sys
import time
import random
from typing import List, Dict, Tuple, Optional

# Add the parent directory to sys.path so Python can find the codenames module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import core game components
from codenames.game import CardType, GameEngine, GameState
from codenames.words import WORD_LIST

# Import AI agents
from codenames.agents.spymaster import SpymasterAgent 
from codenames.agents.operative import OperativeAgent

# Import debate manager
from codenames.agents.debates import DebateManager

# Fix for the 'correct' key bug in generate_guess
def fix_previous_guesses_format(previous_guesses: List[Dict]) -> List[Dict]:
    """Add 'correct' key to guess dictionaries if missing"""
    fixed_guesses = []
    for guess in previous_guesses:
        fixed_guess = guess.copy()
        # If 'correct' key doesn't exist, derive it from card_type
        if 'correct' not in fixed_guess and 'result' in fixed_guess:
            # In the original bug, we need to determine correctness based on the card type
            # If the card type matches the current team, it's correct
            current_team = guess.get('team', 'unknown')
            fixed_guess['correct'] = (fixed_guess['result'] == current_team)
            # Also map result to revealed_type for compatibility
            fixed_guess['revealed_type'] = fixed_guess['result']
        fixed_guesses.append(fixed_guess)
    return fixed_guesses


def display_board(game_state: GameState, show_all: bool = False):
    """Display the game board in a formatted grid
    
    Args:
        game_state: The current game state
        show_all: If True, show all card types (spymaster view),
                 otherwise show only revealed cards (operative view)
    """
    print("\n" + "=" * 50)
    print(f"GAME: {game_state.game_id}")
    print(f"Turn: {game_state.turn}, Current Team: {game_state.current_team.value.upper()}")
    print(f"RED remaining: {game_state.red_remaining}, BLUE remaining: {game_state.blue_remaining}")
    print("=" * 50)
    
    # Calculate the grid dimensions
    size = 5
    
    # Display the board as a grid
    for i in range(size):
        row = game_state.board[i*size:(i+1)*size]
        
        # Display word row
        for card in row:
            print(f"{card.word:<12}", end="")
        print()
        
        # Display card type or index row
        for j, card in enumerate(row):
            idx = i*size + j + 1
            if show_all or card.revealed:
                print(f"[{card.type.value.upper():<10}]", end="")
            else:
                print(f"[{idx:<10}]", end="")
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
                # If it's a boolean, it's probably a result flag, so get the card_type
                card = next((c for c in game_state.board if c.word == guess[1] and c.revealed), None)
                card_type = card.type.value if card else "unknown"
            else:
                card_type = str(guess[2])
                
            print(f"  - {team_name} guessed '{guess[1]}' ({card_type})")
    
    print("=" * 50 + "\n")


def run_debate_example():
    """
    Run a sample debate between AI operatives
    """
    print("\n\n=== CODENAMES DEBATE EXAMPLE ===\n")
    
    # Check for API key
    if not os.environ.get("OPENAI_API_KEY"):
        print("WARNING: No OpenAI API key found in environment variables.")
        print("Please set the OPENAI_API_KEY environment variable.")
        print("For example: export OPENAI_API_KEY='your-api-key-here'")
        api_key = input("\nEnter your OpenAI API key to continue: ").strip()
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
        else:
            print("No API key provided. Exiting.")
            return
    
    # Initialize the game engine
    engine = GameEngine(WORD_LIST)
    
    # Create AI players
    red_spymaster = SpymasterAgent(name="Red Spymaster", team=CardType.RED)
    red_op1 = OperativeAgent(name="Red Op 1", team=CardType.RED)
    red_op2 = OperativeAgent(name="Red Op 2", team=CardType.RED)
    red_team = [red_op1, red_op2]
    
    blue_spymaster = SpymasterAgent(name="Blue Spymaster", team=CardType.BLUE)
    blue_op1 = OperativeAgent(name="Blue Op 1", team=CardType.BLUE)
    blue_op2 = OperativeAgent(name="Blue Op 2", team=CardType.BLUE)
    blue_team = [blue_op1, blue_op2]
    
    # Initialize the debate manager
    debate_manager = DebateManager(max_rounds=2)
    
    # Create a new game
    game_id = engine.create_game()
    game_state = engine.get_game(game_id)
    print(f"Created new game with ID: {game_id}")
    
    # Display the initial board (spymaster view)
    print("\nINITIAL BOARD (SPYMASTER VIEW):")
    display_board(game_state, show_all=True)
    
    # Track both teams' previous guesses
    red_previous_guesses = []
    blue_previous_guesses = []
    
    # Run a single round for each team to demonstrate debate
    for _ in range(1):  # Just one round for the example
        # RED TEAM'S TURN
        print("\n" + "=" * 20 + " RED TEAM'S TURN " + "=" * 20)
        
        # Generate a clue from the red spymaster
        print("\nRed Spymaster is thinking...")
        clue_word, clue_number, target_words = red_spymaster.generate_clue(game_state)
        
        # Process the clue
        engine.process_clue(game_id, clue_word, clue_number, CardType.RED)
        print(f"\nRed Spymaster gives the clue: '{clue_word}' {clue_number}")
        print(f"Target words: {', '.join(target_words)}")
        
        # Team debate for guesses
        correct_guesses = 0
        turn_ongoing = True
        guesses_made = 0
        
        while turn_ongoing and guesses_made < clue_number + 1:
            # Add a short delay for readability
            time.sleep(1)
            
            # Use fix_previous_guesses_format to ensure correct format
            fixed_previous_guesses = fix_previous_guesses_format(red_previous_guesses)
            
            # Team debate to make a decision
            debate_result = debate_manager.run_debate(
                red_team, game_state, clue_word, clue_number, 
                correct_guesses, fixed_previous_guesses
            )
            
            guess = debate_result["final_decision"]
            
            if guess.lower() == "end":
                print("\nRed team decided to end their turn.")
                engine.end_turn(game_id, CardType.RED)
                break
            
            print(f"\nRed team guesses: '{guess}'")
            
            # Process the guess
            guess_result = engine.process_guess(game_id, guess, CardType.RED)
            guesses_made += 1
            
            # Record the guess for future reference
            red_previous_guesses.append({
                "word": guess,
                "result": guess_result["card_type"],
                "team": "red",  # Add team so we can determine correctness later
                "correct": guess_result["card_type"] == "red"  # Explicitly add correct key
            })
            
            # Display the result
            if guess_result["card_type"] == "red":
                print(f"Correct! '{guess}' is a RED card.")
                correct_guesses += 1
            elif guess_result["card_type"] == "assassin":
                print(f"Oh no! '{guess}' is the ASSASSIN card. Game over!")
                turn_ongoing = False
            else:
                opposite_team = "BLUE"
                if guess_result["card_type"] == opposite_team.lower():
                    print(f"Oops! '{guess}' is a {opposite_team} card. Turn ends.")
                else:
                    print(f"'{guess}' is a NEUTRAL card. Turn ends.")
                turn_ongoing = False
            
            # Display the updated board
            display_board(game_state, show_all=False)
            
            # Check if game is over
            if game_state.is_game_over():
                break
            
            # Check if turn should end
            if guess_result["end_turn"]:
                turn_ongoing = False
        
        # End turn if still ongoing
        if turn_ongoing:
            print("Maximum guesses reached. Red team's turn ends.")
            engine.end_turn(game_id, CardType.RED)
        
        # BLUE TEAM'S TURN
        print("\n" + "=" * 20 + " BLUE TEAM'S TURN " + "=" * 20)
        
        # Generate a clue from the blue spymaster
        print("\nBlue Spymaster is thinking...")
        clue_word, clue_number, target_words = blue_spymaster.generate_clue(game_state)
        
        # Process the clue
        engine.process_clue(game_id, clue_word, clue_number, CardType.BLUE)
        print(f"\nBlue Spymaster gives the clue: '{clue_word}' {clue_number}")
        print(f"Target words: {', '.join(target_words)}")
        
        # Team debate for guesses
        correct_guesses = 0
        turn_ongoing = True
        guesses_made = 0
        
        while turn_ongoing and guesses_made < clue_number + 1:
            # Add a short delay for readability
            time.sleep(1)
            
            # Use fix_previous_guesses_format to ensure correct format
            fixed_previous_guesses = fix_previous_guesses_format(blue_previous_guesses)
            
            # Team debate to make a decision
            debate_result = debate_manager.run_debate(
                blue_team, game_state, clue_word, clue_number, 
                correct_guesses, fixed_previous_guesses
            )
            
            guess = debate_result["final_decision"]
            
            if guess.lower() == "end":
                print("\nBlue team decided to end their turn.")
                engine.end_turn(game_id, CardType.BLUE)
                break
            
            print(f"\nBlue team guesses: '{guess}'")
            
            # Process the guess
            guess_result = engine.process_guess(game_id, guess, CardType.BLUE)
            guesses_made += 1
            
            # Record the guess for future reference
            blue_previous_guesses.append({
                "word": guess,
                "result": guess_result["card_type"],
                "team": "blue",  # Add team so we can determine correctness later
                "correct": guess_result["card_type"] == "blue"  # Explicitly add correct key
            })
            
            # Display the result
            if guess_result["card_type"] == "blue":
                print(f"Correct! '{guess}' is a BLUE card.")
                correct_guesses += 1
            elif guess_result["card_type"] == "assassin":
                print(f"Oh no! '{guess}' is the ASSASSIN card. Game over!")
                turn_ongoing = False
            else:
                opposite_team = "RED"
                if guess_result["card_type"] == opposite_team.lower():
                    print(f"Oops! '{guess}' is a {opposite_team} card. Turn ends.")
                else:
                    print(f"'{guess}' is a NEUTRAL card. Turn ends.")
                turn_ongoing = False
            
            # Display the updated board
            display_board(game_state, show_all=False)
            
            # Check if game is over
            if game_state.is_game_over():
                break
            
            # Check if turn should end
            if guess_result["end_turn"]:
                turn_ongoing = False
        
        # End turn if still ongoing
        if turn_ongoing:
            print("Maximum guesses reached. Blue team's turn ends.")
            engine.end_turn(game_id, CardType.BLUE)
    
    # Display the final board state
    print("\nFINAL BOARD STATE:")
    display_board(game_state, show_all=True)
    
    print("\nDebate example completed. This demonstrates how to use the DebateManager")
    print("to facilitate multi-agent decision making in the Codenames game.")


if __name__ == "__main__":
    # Run the debate example
    run_debate_example()
