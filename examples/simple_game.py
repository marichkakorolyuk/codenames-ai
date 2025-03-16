#!/usr/bin/env python3
"""
Codenames Simple Game Example

This file demonstrates the basic functionality of the Codenames game engine
without AI agents or debates. It shows how to:

1. Create a new game
2. Display the game board
3. Process clues and guesses, including invalid ones
4. Loop the game until completion

This serves as a simple introduction to the game's core functionality.
"""

import os
import sys
import random
from typing import List, Dict
from pprint import pprint

# Add the parent directory to sys.path so Python can find the codenames module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import core game components
from codenames.game import CardType, GameEngine, GameState, print_board
from codenames.words import WORD_LIST


def print_divider():
    """Print a visual divider for readability"""
    print("\n" + "-" * 80 + "\n")


def get_valid_cards_for_team(game_state, team):
    """Get list of unrevealed card words for a specific team
    
    Args:
        game_state: Current game state
        team: The team (CardType.RED or CardType.BLUE)
        
    Returns:
        List of card words belonging to the team that haven't been revealed yet
    """
    valid_cards = []
    for card in game_state.board:
        if not card.revealed and card.type == team:
            valid_cards.append(card.word)
    return valid_cards


def main():
    """Run the simple game example"""
    print("\n\n=== CODENAMES SIMPLE GAME EXAMPLE ===\n")
    
    # Initialize the game engine with the standard word list
    engine = GameEngine(WORD_LIST)

    # Create a new game (the engine generates a random game ID)
    game_id = engine.create_game(seed=0)
    print(f"Created new game with ID: {game_id}")
    game_state = engine.get_game(game_id)
    print_board(game_state)
    
    print_divider()
    print("MAKING INVALID GUESSES")
    
    # Example 1: Process a clue with invalid format
    clue_word = "travel"
    clue_number = 2

    # Those are strings! For simplicity, supposedly :) 
    selected_cards = []

    for card in game_state.board:
        if not (card.revealed) and card.type == game_state.current_team:
            selected_cards.append(card.word)
            
            if len(selected_cards) == clue_number:
                break

    # Invalid guess with emoji and spacing
    try:
        result = engine.process_clue(game_id, clue_word, ['banana 🧐🤙 invalid'], game_state.current_team)
    except ValueError as e:
        print(f"Error with invalid card format: {e}")

    # Valid clue
    result = engine.process_clue(game_id, clue_word, selected_cards, game_state.current_team)
    print(f"Processing clue '{clue_word}' {selected_cards}: {'Success' if result else 'Failed'}")
    
    # Example 2: Guess a card that doesn't exist
    try:
        result = engine.process_guess(game_id, "nonexistent_card", game_state.current_team)
        print(f"Result of guessing nonexistent card: {result}")
    except ValueError as e:
        print(f"Error guessing nonexistent card: {e}")
    
    # Example The Spice Girls: Process a clue with wrong team (not the current team's turn)
    wrong_team = CardType.BLUE if game_state.current_team == CardType.RED else CardType.RED
    try:
        result = engine.process_clue(game_id, "wrong_team_clue", selected_cards, wrong_team)
    except ValueError as e:
        print(f"Error with wrong team: {e}")
    
    print_divider()
    print("STARTING GAME LOOP")
    
    # Now, loop the game until it's finished
    # For simplicity, we'll make a single-word clue each turn and guess that word
    turn_count = 0
    max_turns = 15  # Safety to avoid infinite loops
    
    while not game_state.is_game_over() and turn_count < max_turns:
        turn_count += 1
        print(f"\nTurn {turn_count} - {game_state.current_team.value.upper()} TEAM")
        current_team = game_state.current_team
        
        # Get valid cards for the current team
        team_cards = get_valid_cards_for_team(game_state, current_team)
        
        if not team_cards:
            print(f"No more cards for {current_team.value} team!")
            engine.end_turn(game_id, current_team)
            continue
        
        # Take one card at a time for simplicity
        selected_card = team_cards[0]
        
        # Generate a simple clue (just use the card word itself in this example)
        # In a real game, the spymaster would give a clever clue related to the word
        clue_word = f"clue_for_{selected_card}"
        
        print(f"Giving clue: '{clue_word}' 1")
        engine.process_clue(game_id, clue_word, [selected_card], current_team)
        
        # Make the guess
        print(f"Guessing: '{selected_card}'")
        result = engine.process_guess(game_id, selected_card, current_team)
        
        if result["success"]:
            card_type = result["card_type"]
            print(f"  Card type: {card_type}")
            print(f"  Current team guessed {'correctly' if card_type == current_team.value else 'incorrectly'}")
            
            if result.get("game_over", False):
                winner = result.get("winner")
                print(f"\nGAME OVER! {winner.upper()} team wins!")
                break
        else:
            print(f"  Guess failed: {result}")
        
        # If the guess ended the turn or we want to end it manually
        if result.get("end_turn", False) or card_type != current_team.value:
            print(f"  Turn ended.")
        else:
            # End the turn manually for this example
            # In a real game, a team might make multiple guesses before ending their turn
            engine.end_turn(game_id, current_team)
            print(f"  Manually ending turn.")
        
        # Print updated board after each turn

        print(f"Red remaining: {game_state.red_remaining}, Blue remaining: {game_state.blue_remaining}")
        
    if not game_state.is_game_over():
        print("\nMaximum turns reached without a winner.")
    
    print("\nFinal board:")
    print_board(game_state)
    
    if game_state.winner:
        print(f"\nWinner: {game_state.winner.value.upper()} TEAM")
    else:
        print("\nNo winner determined.")


if __name__ == "__main__":
    main()
