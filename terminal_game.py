#!/usr/bin/env python3
"""
Codenames Terminal Game - with AI support through OpenAI API.
This file enables playing Codenames through the terminal with a mix of AI and human players.
"""

import os
import sys
import random
from typing import Dict, List, Optional, Tuple, Union, Any
import openai
from game_core import GameEngine, CardType, Card, GameState
from words import WORD_LIST

class PlayerRole:
    SPYMASTER = "spymaster"
    OPERATIVE = "operative"

class PlayerType:
    HUMAN = "human"
    AI = "ai"

class Player:
    def __init__(self, name: str, role: str, player_type: str, team: CardType):
        self.name = name
        self.role = role  # "spymaster" or "operative"
        self.type = player_type  # "human" or "ai"
        self.team = team  # CardType.RED or CardType.BLUE

class TerminalGameManager:
    def __init__(self, openai_api_key: Optional[str] = None):
        self.engine = GameEngine(WORD_LIST)
        self.game_id = None
        self.players: List[Player] = []
        
        # OpenAI setup
        if openai_api_key:
            openai.api_key = openai_api_key
        elif os.environ.get("OPENAI_API_KEY"):
            openai.api_key = os.environ.get("OPENAI_API_KEY")
        
        # Set default client if API key is provided
        self.client = None
        if openai.api_key:
            self.client = openai.OpenAI()
    
    def setup_game(self):
        """Set up a new game with players"""
        print("\n=== CODENAMES TERMINAL GAME ===\n")
        
        # Check for OpenAI API key
        if not openai.api_key and self._prompt_yes_no("Do you want to use AI players? (requires OpenAI API key)"):
            api_key = input("Enter your OpenAI API key: ").strip()
            if api_key:
                openai.api_key = api_key
                self.client = openai.OpenAI(model='gpt-4o')
                print("OpenAI API key set successfully!")
            else:
                print("No API key provided. Proceeding with human players only.")
        
        # Create new game
        self.game_id = self.engine.create_game()
        game_state = self.engine.get_game(self.game_id)
        
        # Setup teams
        print(f"\nFirst team: {game_state.current_team.value.upper()}")
        
        self._setup_team(CardType.RED)
        self._setup_team(CardType.BLUE)
        
        print("\nGame setup complete! Starting game...\n")
        self.play_game()
    
    def _setup_team(self, team: CardType):
        """Setup players for a team"""
        team_name = team.value.upper()
        print(f"\n--- {team_name} TEAM SETUP ---")
        
        # Spymaster setup
        spymaster_type = self._prompt_player_type(f"{team_name} Spymaster")
        spymaster_name = f"{team_name} Spymaster"
        if spymaster_type == PlayerType.HUMAN:
            spymaster_name = input(f"Enter name for {team_name} Spymaster: ").strip() or spymaster_name
        
        self.players.append(Player(
            name=spymaster_name,
            role=PlayerRole.SPYMASTER,
            player_type=spymaster_type,
            team=team
        ))
        
        # Operatives setup
        operative_type = self._prompt_player_type(f"{team_name} Operative")
        operative_name = f"{team_name} Operative"
        if operative_type == PlayerType.HUMAN:
            operative_name = input(f"Enter name for {team_name} Operative: ").strip() or operative_name
        
        self.players.append(Player(
            name=operative_name,
            role=PlayerRole.OPERATIVE,
            player_type=operative_type,
            team=team
        ))
    
    def _prompt_player_type(self, role_name: str) -> str:
        """Prompt to choose AI or human for a role"""
        # If no API key, default to human
        if not openai.api_key:
            return PlayerType.HUMAN
            
        while True:
            choice = input(f"Choose player type for {role_name} (H for Human, A for AI): ").strip().upper()
            if choice == 'H':
                return PlayerType.HUMAN
            elif choice == 'A':
                return PlayerType.AI
            else:
                print("Invalid choice. Please enter 'H' or 'A'.")
    
    def _prompt_yes_no(self, question: str) -> bool:
        """Prompt for a yes/no question"""
        while True:
            choice = input(f"{question} (y/n): ").strip().lower()
            if choice in ['y', 'yes']:
                return True
            elif choice in ['n', 'no']:
                return False
            else:
                print("Invalid choice. Please enter 'y' or 'n'.")
    
    def _get_current_player(self, role: str) -> Optional[Player]:
        """Get the current player based on team and role"""
        game_state = self.engine.get_game(self.game_id)
        current_team = game_state.current_team
        
        for player in self.players:
            if player.team == current_team and player.role == role:
                return player
        return None
    
    def _display_board(self, for_spymaster: bool = False):
        """Display the game board"""
        game_state = self.engine.get_game(self.game_id)
        
        print("\n----- GAME BOARD -----")
        print(f"RED: {game_state.red_remaining} left | BLUE: {game_state.blue_remaining} left")
        print(f"Current turn: {game_state.current_team.value.upper()}")
        print()
        
        # Display board in a 5x5 grid
        for i in range(5):
            row = []
            for j in range(5):
                card = game_state.board[i * 5 + j]
                if card.revealed:
                    # Show revealed cards with their type
                    card_display = f"{card.word.ljust(12)} ({card.type.value})"
                elif for_spymaster:
                    # Show unrevealed cards with their type for spymaster
                    card_display = f"{card.word.ljust(12)} ({card.type.value})"
                else:
                    # Show only the word for operatives
                    card_display = card.word.ljust(12)
                row.append(card_display)
            print(" | ".join(row))
        print()
        
        # Display clue history
        if game_state.clue_history:
            print("--- CLUE HISTORY ---")
            for team, clue, number in game_state.clue_history:
                print(f"{team.value.upper()}: \"{clue}\" for {number}")
        
        print("-----------------------\n")
    
    def _get_ai_clue(self, spymaster: Player) -> Tuple[str, int]:
        """Get a clue from an AI spymaster"""
        game_state = self.engine.get_game(self.game_id)
        board_state = game_state.get_spymaster_state(spymaster.team)
        
        # Prepare the message for the AI
        team_words = []
        opponent_words = []
        
        for card in game_state.board:
            if not card.revealed:
                if card.type == spymaster.team:
                    team_words.append(card.word)
                elif card.type in [CardType.RED, CardType.BLUE]:
                    opponent_words.append(card.word)
                elif card.type == CardType.ASSASSIN:
                    assassin_word = card.word
        
        prompt = f"""
You are the {spymaster.team.value} Spymaster in a game of Codenames. You need to give a one-word clue and a number.
The number indicates how many words on the board your clue relates to.

Your team's words (that your operatives need to guess): {', '.join(team_words)}
Opponent's words (to avoid): {', '.join(opponent_words)}
Assassin word (must avoid at all costs): {assassin_word}

Give a one-word clue and a number that connects multiple words for your team while avoiding the opponent's words and especially the assassin.
Respond with only the clue word and number, separated by a space. For example: "travel 2"
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a Codenames Spymaster AI."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=20
            )
            
            # Parse the response
            clue_text = response.choices[0].message.content.strip()
            parts = clue_text.split()
            if len(parts) >= 2 and parts[-1].isdigit():
                return parts[0], int(parts[-1])
            else:
                # Fallback if format is incorrect
                return clue_text, 1
                
        except Exception as e:
            print(f"Error getting AI clue: {e}")
            # Fallback to a random clue if API fails
            return random.choice(["fallback", "emergency", "backup"]), 1
    
    def _get_ai_guess(self, operative: Player, clue: str, number: int) -> str:
        """Get a guess from an AI operative"""
        game_state = self.engine.get_game(self.game_id)
        board_state = game_state.get_visible_state(operative.team)
        
        # Create a list of unrevealed words
        unrevealed_words = []
        for card in game_state.board:
            if not card.revealed:
                unrevealed_words.append(card.word)
        
        # Prepare the message for the AI
        prompt = f"""
You are the {operative.team.value} team Operative in a game of Codenames.

The Spymaster gave the clue: "{clue}" for {number} words.

The unrevealed words on the board are: {', '.join(unrevealed_words)}

Based on the clue, which word do you think is most likely to be one of your team's words?
Choose exactly one word from the list. Respond with only that word.
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a Codenames Operative AI."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=20
            )
            
            guess = response.choices[0].message.content.strip().lower()
            
            # Check if the guess is in the list of unrevealed words
            if guess in [card.word.lower() for card in game_state.board if not card.revealed]:
                return guess
            else:
                # If AI returns an invalid word, choose randomly from unrevealed words
                print(f"AI made an invalid guess: {guess}")
                return random.choice(unrevealed_words)
                
        except Exception as e:
            print(f"Error getting AI guess: {e}")
            # Fallback to a random guess if API fails
            return random.choice(unrevealed_words)
    
    def play_game(self):
        """Main game loop"""
        game_state = self.engine.get_game(self.game_id)
        
        while not game_state.winner:
            current_team = game_state.current_team
            current_spymaster = self._get_current_player(PlayerRole.SPYMASTER)
            current_operative = self._get_current_player(PlayerRole.OPERATIVE)
            
            # Display the board (different views for different players)
            if current_spymaster.type == PlayerType.HUMAN:
                print(f"\n{current_spymaster.name}'s turn (Spymaster)")
                self._display_board(for_spymaster=True)
            
            # Get clue from spymaster
            clue_word, clue_number = "", 0
            
            if current_spymaster.type == PlayerType.HUMAN:
                while True:
                    try:
                        clue_input = input("Enter your clue (word number): ").strip().split()
                        if len(clue_input) >= 2 and clue_input[-1].isdigit():
                            clue_word = clue_input[0]
                            clue_number = int(clue_input[-1])
                            break
                        else:
                            print("Invalid format. Please enter a word followed by a number.")
                    except ValueError:
                        print("Invalid number. Please try again.")
            else:
                print(f"\n{current_spymaster.name} (AI) is thinking...")
                clue_word, clue_number = self._get_ai_clue(current_spymaster)
            
            # Process the clue
            success = self.engine.process_clue(self.game_id, clue_word, clue_number, current_team)
            if not success:
                print("Error processing clue. Please try again.")
                continue
            
            print(f"\n{current_spymaster.name} gives the clue: \"{clue_word}\" for {clue_number}")
            
            # Operatives guessing phase
            guesses_left = clue_number + 1  # Can guess one more than the clue number
            continue_guessing = True
            
            while continue_guessing and guesses_left > 0 and not game_state.winner:
                if current_operative.type == PlayerType.HUMAN:
                    print(f"\n{current_operative.name}'s turn (Operative)")
                    self._display_board(for_spymaster=False)
                    print(f"Clue: \"{clue_word}\" for {clue_number}. Guesses left: {guesses_left}")
                    
                    # Display options for guessing
                    guess_options = [card.word for card in game_state.board if not card.revealed]
                    
                    # Ask for guess or end turn
                    choice = input("Make a guess or type 'end' to end your turn: ").strip().lower()
                    
                    if choice == 'end':
                        continue_guessing = False
                        self.engine.end_turn(self.game_id, current_team)
                        break
                    
                    guess_word = choice
                else:
                    print(f"\n{current_operative.name} (AI) is thinking...")
                    self._display_board(for_spymaster=False)
                    guess_word = self._get_ai_guess(current_operative, clue_word, clue_number)
                    print(f"{current_operative.name} guesses: {guess_word}")
                
                # Process the guess
                result = self.engine.process_guess(self.game_id, guess_word, current_team)
                
                if not result:
                    print("Invalid guess. Please try again.")
                    continue
                
                if not result.get("success", False):
                    print(f"Error: {result.get('error', 'Unknown error')}")
                    continue
                
                # Display result of the guess
                card_type = result.get("card_type", "unknown")
                print(f"The word \"{guess_word}\" is a {card_type.upper()} card!")
                
                # Check if the game is over
                if result.get("game_over", False):
                    winner = result.get("winner", "unknown")
                    print(f"\nGAME OVER! The {winner.upper()} team wins!")
                    break
                
                # Check if turn ended
                if result.get("end_turn", True):
                    print(f"Turn ends for {current_team.value.upper()} team.")
                    continue_guessing = False
                else:
                    guesses_left -= 1
                    if guesses_left <= 0:
                        print("No more guesses left. Turn ends.")
                        continue_guessing = False
                        self.engine.end_turn(self.game_id, current_team)
            
            # Refresh game state for next iteration
            game_state = self.engine.get_game(self.game_id)
        
        # Game over
        print("\n=== GAME OVER ===")
        print(f"The {game_state.winner.value.upper()} team wins!")
        self._display_board(for_spymaster=True)

def main():
    # Check for OpenAI API key in environment
    api_key = os.environ.get("OPENAI_API_KEY")
    
    # Create game manager
    game_manager = TerminalGameManager(api_key)
    
    # Setup and start the game
    game_manager.setup_game()

if __name__ == "__main__":
    main()
