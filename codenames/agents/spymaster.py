"""
Spymaster AI agents for Codenames game.
Contains AI implementations for the Spymaster role.
"""

import re
import random
from typing import Dict, List, Tuple, Any, Optional

import openai
from ..game import GameState, CardType


class SpymasterAgent:
    """AI agent that plays as a Spymaster"""
    def __init__(self, name: str, team: CardType, model: str = "gpt-4o"):
        self.name = name
        self.team = team
        self.role = "spymaster"
        self.model = model
        self.decisions: List[Dict[str, Any]] = []
    
    def make_api_call(self, system_message: str, user_message: str) -> str:
        """Make an API call to the language model"""
        try:
            client = openai.OpenAI()
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                max_tokens=500
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error making API call: {e}")
            return f"Error: {str(e)[:100]}..."
    
    def generate_clue(self, game_state: GameState) -> Tuple[str, int, List[str]]:
        """Generate a clue based on the game state"""
        board_state = game_state.get_spymaster_state(self.team)
        
        # Gather words by type
        team_words = []
        opponent_words = []
        assassin_word = ""
        neutral_words = []
        
        for card in game_state.board:
            if not card.revealed:
                if card.type == self.team:
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
You are the {self.team.value} Spymaster in a game of Codenames. You need to give a one-word clue and a number.
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
- Be creative but clear - your operatives must understand your thinking.

You MUST respond in EXACTLY this format:
CLUE: [your_clue_word]
NUMBER: [number_of_words]
TARGETS: [word1], [word2], etc.

The TARGETS must be words from your team's list above, and the NUMBER must match the count of TARGETS.
"""
        
        response_text = self.make_api_call(
            "You are a Codenames Spymaster AI focused on efficiency.", 
            prompt
        )
        
        # Extract clue, number, and targets
        clue_word = ""
        clue_number = 0
        target_words = []
        
        try:
            # Parse with regular expressions
            clue_match = re.search(r"CLUE:\s*([\w\-]+)", response_text, re.IGNORECASE)
            if clue_match:
                clue_word = clue_match.group(1).strip()
            
            number_match = re.search(r"NUMBER:\s*(\d+)", response_text, re.IGNORECASE)
            if number_match:
                clue_number = int(number_match.group(1))
            
            targets_match = re.search(r"TARGETS:\s*(.*?)(?:\n|$)", response_text, re.IGNORECASE)
            if targets_match:
                targets_text = targets_match.group(1).strip()
                raw_targets = [word.strip() for word in targets_text.split(',')]
                
                # Match targets to team words (case-insensitive)
                for target in raw_targets:
                    for team_word in team_words:
                        if team_word.lower() == target.lower():
                            target_words.append(team_word)
                            break
        except Exception as parse_error:
            print(f"Error parsing response: {parse_error}")
        
        # Handle parsing failures and ensure consistency
        if not clue_word:
            words = response_text.split()
            if words:
                clue_word = words[0].strip()
        
        if target_words:
            if clue_number != len(target_words):
                clue_number = len(target_words)
        elif clue_number > 0:
            # Infer targets by word similarity if needed
            potential_targets = sorted(team_words, 
                                      key=lambda word: self._simple_word_similarity(clue_word, word),
                                      reverse=True)
            target_words = potential_targets[:min(clue_number, len(potential_targets))]
        elif clue_number <= 0:
            clue_number = 1
            if team_words:
                target_words = [random.choice(team_words)]
        
        # Log the decision
        self.decisions.append({
            "type": "clue",
            "prompt": prompt,
            "response": response_text,
            "parsed": {
                "word": clue_word,
                "number": clue_number,
                "targets": target_words
            }
        })
        
        print(f"{self.name} gives clue: {clue_word}, Number: {clue_number}, Targets: {target_words}")
        return clue_word, clue_number, target_words
    
    def _simple_word_similarity(self, word1: str, word2: str) -> float:
        """A basic similarity measure between words"""
        word1, word2 = word1.lower(), word2.lower()
        
        if word1 == word2:
            return 1.0
        if word1 in word2 or word2 in word1:
            return 0.8
        
        set1, set2 = set(word1), set(word2)
        shared = len(set1.intersection(set2))
        total = len(set1.union(set2))
        
        return shared / total if total > 0 else 0.0
