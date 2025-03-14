"""
Operative AI agents for Codenames game.
Contains AI implementations for the Operative role.
"""

import re
import random
from typing import Dict, List, Tuple, Any, Optional

import openai
from ..game import GameState, CardType


class OperativeAgent:
    """AI agent that plays as an Operative"""
    def __init__(self, name: str, team: CardType, model: str = "gpt-4o"):
        self.name = name
        self.team = team
        self.role = "operative"
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
    
    def generate_guess(self, game_state: GameState, clue: str, number: int, 
                       correct_guesses: int, previous_guesses: List[Dict]) -> Tuple[str, str]:
        """Generate a guess based on the clue and game state
        Returns a tuple of (guess_word, reasoning)
        """
        board_state = game_state.get_visible_state(self.team)
        
        # Create lists of revealed and unrevealed words
        unrevealed_words = []
        revealed_words = []
        for card in game_state.board:
            if not card.revealed:
                unrevealed_words.append(card.word)
            else:
                revealed_words.append(card.word)
        
        # Format previous guesses for the prompt
        previous_guesses_text = ""
        if previous_guesses:
            previous_guesses_text = "Previous guesses this turn:\n"
            for i, guess in enumerate(previous_guesses):
                result_text = "CORRECT" if guess["correct"] else "INCORRECT"
                card_type = guess.get("revealed_type", "unknown")
                previous_guesses_text += f"{i+1}. '{guess['word']}' - {result_text} (was a {card_type} card)\n"
        
        # Format revealed words by type
        revealed_by_type = {"red": [], "blue": [], "neutral": [], "assassin": []}
        for card in game_state.board:
            if card.revealed:
                revealed_by_type[card.type.value].append(card.word)
        
        # Create prompt with all context
        prompt = f"""
You are the {self.team.value} Operative in a game of Codenames. Your Spymaster has given the clue:
'{clue}' {number}

This means there are {number} words on the board related to this clue that you should try to guess.

Current board state:
- Unrevealed words: {', '.join(unrevealed_words)}
- Revealed Red Team words: {', '.join(revealed_by_type['red'])}
- Revealed Blue Team words: {', '.join(revealed_by_type['blue'])}
- Revealed Neutral words: {', '.join(revealed_by_type['neutral'])}
- Revealed Assassin words: {', '.join(revealed_by_type['assassin'])}

Game situation:
- You are on the {self.team.value.upper()} team
- Red team has {board_state['red_remaining']} words remaining
- Blue team has {board_state['blue_remaining']} words remaining
- You have made {correct_guesses} correct guesses for this clue so far
- You can make up to {number+1-correct_guesses} more guesses this turn
{previous_guesses_text}

Your task is to guess ONE word from the unrevealed words that you think is most related to the clue '{clue}'.
If you are uncertain about any remaining words, or if you've already guessed all the words you think are connected
to the clue, you should consider ending your turn by saying 'end'.

You MUST respond in EXACTLY this format:
DECISION: [your_chosen_word_or_end]
REASONING: [detailed explanation of your thought process]

Choose the word that you believe has the strongest connection to the clue '{clue}',
or 'end' if you want to end your turn.
"""
        
        response_text = self.make_api_call(
            "You are a Codenames Operative AI. Your goal is to correctly identify words related to your Spymaster's clue.",
            prompt
        )
        
        # Parse the AI response
        decision_match = re.search(r"DECISION:\s*([^\n]+)", response_text, re.IGNORECASE)
        reasoning_match = re.search(r"REASONING:\s*(.*)", response_text, re.IGNORECASE | re.DOTALL)
        
        guess_word = "end"  # Default to ending turn if parsing fails
        reasoning = "No clear reasoning provided."
        
        if decision_match:
            guess_word = decision_match.group(1).strip().lower()
            
            # Clean up potential quotes in the decision
            guess_word = guess_word.strip("'\"")
            
            # Validate the guess is an actual unrevealed word or "end"
            if guess_word != "end" and guess_word not in [w.lower() for w in unrevealed_words]:
                # Try to find closest match in unrevealed words
                best_match = None
                highest_similarity = 0
                for word in unrevealed_words:
                    similarity = self._simple_word_similarity(guess_word, word.lower())
                    if similarity > highest_similarity:
                        highest_similarity = similarity
                        best_match = word
                
                if highest_similarity > 0.7 and best_match:  # High confidence threshold
                    guess_word = best_match.lower()
                else:
                    guess_word = "end"
        
        if reasoning_match:
            reasoning = reasoning_match.group(1).strip()
        
        # Log the decision
        self.decisions.append({
            "type": "guess",
            "prompt": prompt,
            "response": response_text,
            "parsed": {
                "guess": guess_word,
                "reasoning": reasoning
            }
        })
        
        return guess_word, reasoning
    
    def debate_response(self, debate_log: List[Dict[str, Any]], game_state: GameState, 
                       clue: str, number: int) -> str:
        """Generate a response to the ongoing debate"""
        board_state = game_state.get_visible_state(self.team)
        
        unrevealed_words = [card.word for card in game_state.board if not card.revealed]
        
        # Construct debate summary
        debate_summary = ""
        for entry in debate_log:
            debate_summary += f"{entry['agent']}: {entry['message'][:200]}...\n\n"
        
        prompt = f"""
You are participating in a team debate for Codenames as the {self.team.value} Operative.
Your Spymaster has given the clue '{clue}' {number}.

DEBATE SO FAR:
{debate_summary}

CURRENT BOARD:
Unrevealed words: {', '.join(unrevealed_words)}

As a team member, respond to the ongoing debate. You should:
1. State your current opinion about the best guess
2. Respond directly to points made by other team members
3. Explain your reasoning clearly
4. If you've changed your mind based on others' arguments, explain why

Please keep your response under 200 words.
"""
        
        response = self.make_api_call(
            "You are a Codenames Operative participating in a team discussion.",
            prompt
        )
        
        return response
    
    def final_vote(self, debate_log: List[Dict[str, Any]], options: List[str], 
                  game_state: GameState, clue: str, number: int) -> str:
        """Cast a final vote on which word to guess"""
        unrevealed_words = [card.word for card in game_state.board if not card.revealed]
        
        # Construct debate summary - focus on the later rounds which are more important
        later_rounds = [entry for entry in debate_log if entry['round'] > 1]
        debate_summary = ""
        for entry in later_rounds[-3:]:  # Take the last few entries to keep it focused
            debate_summary += f"{entry['agent']}: {entry['message'][:150]}...\n\n"
        
        prompt = f"""
You are casting your final vote in a Codenames team debate as the {self.team.value} Operative.
The clue was '{clue}' {number}.

FINAL DEBATE SUMMARY:
{debate_summary}

OPTIONS TO VOTE FOR:
{', '.join(options)}

Based on the debate and your own analysis, cast a single vote for one of the options above.
Consider:
1. Which word has the strongest connection to the clue '{clue}'
2. The arguments made by your teammates
3. Whether it might be safer to end the turn

You MUST vote for one of the exact options listed above.
Respond with just the word you're voting for.
"""
        
        vote = self.make_api_call(
            "You are a Codenames Operative making a final decision.",
            prompt
        ).strip().lower()
        
        # Clean up potential formatting or quotes
        vote = vote.strip("'\".,!? ")
        
        # Ensure the vote is valid
        if vote not in [option.lower() for option in options]:
            # Default to "end" if invalid
            print(f"Invalid vote '{vote}' from {self.name}. Defaulting to 'end'.")
            vote = "end"
        
        return vote

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
