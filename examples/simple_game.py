#!/usr/bin/env python3
"""
Codenames Simple Game Example

This file demonstrates the basic functionality of the Codenames game engine
without AI agents or debates. It shows how to:

1. Create a new game
2. Display the game board
3. Process clues and guesses
4. Track game state and turns

This serves as a simple introduction to the game's core functionality.
"""

import os
import sys
import random
from typing import List, Dict

# Add the parent directory to sys.path so Python can find the codenames module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import core game components
from codenames.game import CardType, GameEngine, GameState
from codenames.words import WORD_LIST


def display_board(game_state: GameState, show_all: bool = False):
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


def get_human_input(prompt: str, options: List[str] = None) -> str:
    """
    Get input from a human player with validation.
    
    Args:
        prompt: The prompt to display
        options: Optional list of valid options
        
    Returns:
        The validated input
    """
    while True:
        value = input(prompt).strip()
        
        if not options:
            return value
        
        if value.lower() in [opt.lower() for opt in options]:
            return value
        
        print(f"Invalid choice. Please choose from: {', '.join(options)}")


def play_simple_game():
    """
    Simple game setup and play
    
    This example demonstrates how to:
    - Create a new game with the GameEngine
    - Access game state
    - Display the board
    - Process clues and guesses
    - End turns and track game progress
    """
    print("\n\n=== CODENAMES SIMPLE GAME EXAMPLE ===\n")
    
    # Initialize the game engine with the standard word list
    engine = GameEngine(WORD_LIST)
    
    # Create a new game (the engine generates a random game ID)
    game_id = engine.create_game()
    print(f"Created new game with ID: {game_id}")
    
    # Get the game state
    game_state = engine.get_game(game_id)
    
    # Display the board - spymaster view (showing all card types)
    print("\nSPYMASTER VIEW:")
    display_board(game_state, show_all=True)
    
    # Display the board - operative view (only showing revealed cards)
    print("\nOPERATIVE VIEW:")
    display_board(game_state, show_all=False)
    
    # Manually process a clue and guess
    print("\nMANUAL GAMEPLAY EXAMPLE:")
    
    # Process a clue for the current team
    clue_word = "travel"
    clue_number = 2
    result = engine.process_clue(game_id, clue_word, clue_number, game_state.current_team)
    print(f"Processing clue '{clue_word}' {clue_number}: {'Success' if result else 'Failed'}")
    
    # Find a valid card to guess for the current team
    team_card = None
    for card in game_state.board:
        if card.type == game_state.current_team and not card.revealed:
            team_card = card
            break
    
    # Process a guess
    if team_card:
        guess_result = engine.process_guess(game_id, team_card.word, game_state.current_team)
        print(f"Guessing '{team_card.word}': {guess_result}")
        
        # Display the updated board
        print("\nOPERATIVE VIEW AFTER GUESS:")
        display_board(game_state, show_all=False)
    
    # End the turn
    current_team = game_state.current_team
    engine.end_turn(game_id, current_team)
    print(f"\nEnding turn for {current_team.value.upper()} team")
    print(f"New current team: {game_state.current_team.value.upper()}")
    
    # Process a clue for the next team
    clue_word = "nature"
    clue_number = 3
    result = engine.process_clue(game_id, clue_word, clue_number, game_state.current_team)
    print(f"\nProcessing clue '{clue_word}' {clue_number} for {game_state.current_team.value.upper()} team: {'Success' if result else 'Failed'}")
    
    # Find a card belonging to the other team to demonstrate incorrect guesses
    opponent_card = None
    for card in game_state.board:
        if card.type != game_state.current_team and not card.revealed:
            opponent_card = card
            break
    
    # Process an incorrect guess
    if opponent_card:
        guess_result = engine.process_guess(game_id, opponent_card.word, game_state.current_team)
        print(f"Guessing '{opponent_card.word}': {guess_result}")
        
        # Display the updated board
        print("\nOPERATIVE VIEW AFTER INCORRECT GUESS:")
        display_board(game_state, show_all=False)
    
    print("\nThis demonstrates the basic game functionality without AI agents.")
    print("Try creating your own games and gameplay logic using these core components!")


if __name__ == "__main__":
    # Run the simple game example
    play_simple_game()
