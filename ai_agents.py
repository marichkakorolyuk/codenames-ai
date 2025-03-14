"""
AI Agents for Codenames
Contains definitions for different AI agents that can play Codenames
"""

import random
import re
from typing import Dict, List, Tuple, Any, Optional
import openai
from game_core import GameState, CardType

class AIAgent:
    """Base class for all AI agents"""
    def __init__(self, name: str, model: str = "gpt-4o"):
        self.name = name
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

class SpymasterAgent(AIAgent):
    """AI agent that plays as a Spymaster"""
    def __init__(self, name: str, team: CardType, model: str = "gpt-4o"):
        super().__init__(name, model)
        self.team = team
        self.role = "spymaster"
    
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

class OperativeAgent(AIAgent):
    """AI agent that plays as an Operative"""
    def __init__(self, name: str, team: CardType, model: str = "gpt-4o"):
        super().__init__(name, model)
        self.team = team
        self.role = "operative"
    
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
                revealed_words.append({"word": card.word, "type": card.type.value})
        
        # Include info about previous guesses for this clue
        previous_guesses_str = ""
        if previous_guesses:
            previous_guesses_str = "Previous guesses for this clue:\n"
            for guess in previous_guesses:
                correct_mark = "✓" if guess.get("is_correct", False) else "✗"
                previous_guesses_str += f"- {guess['word']} ({guess['actual_type']}) {correct_mark}\n"
        
        prompt = f"""
You are the {self.team.value} team Operative in a game of Codenames.

The Spymaster gave the clue: "{clue}" for {number} words.
So far, your team has made {correct_guesses} correct guesses for this clue.

The unrevealed words on the board are: {', '.join(unrevealed_words)}

Previously revealed words: {', '.join([f"{w['word']} ({w['type']})" for w in revealed_words])}

{previous_guesses_str}

INSTRUCTIONS:
1. Analyze how the clue "{clue}" might relate to the unrevealed words.
2. Provide a detailed explanation of your reasoning.
3. End with your guess or a decision to end the turn.

Respond in this format:
REASONING: [Your detailed analysis of the clue and possible words]
DECISION: [ONE specific word from the board OR "END" to end your turn]
"""
        
        response_text = self.make_api_call(
            "You are a Codenames Operative AI. Explain your reasoning clearly.", 
            prompt
        )
        
        # Extract reasoning and decision
        reasoning = ""
        decision = ""
        
        reasoning_match = re.search(r"REASONING:\s*(.*?)(?:DECISION:|$)", response_text, re.DOTALL | re.IGNORECASE)
        if reasoning_match:
            reasoning = reasoning_match.group(1).strip()
        
        decision_match = re.search(r"DECISION:\s*(.*?)(?:\n|$)", response_text, re.IGNORECASE)
        if decision_match:
            decision = decision_match.group(1).strip().lower()
        
        # If we couldn't parse properly, use fallbacks
        if not reasoning:
            reasoning = response_text
        
        if not decision:
            # Check for a word or "end" in the last line
            lines = response_text.strip().split('\n')
            if lines:
                last_line = lines[-1].lower()
                if "end" in last_line:
                    decision = "end"
                else:
                    # Look for one of the unrevealed words in the last few lines
                    for i in range(min(3, len(lines))):
                        for word in unrevealed_words:
                            if word.lower() in lines[-(i+1)].lower():
                                decision = word.lower()
                                break
                        if decision:
                            break
            
            # If still no decision, default to first word mentioned in reasoning that's on the board
            if not decision:
                for word in unrevealed_words:
                    if word.lower() in reasoning.lower():
                        decision = word.lower()
                        break
        
        # Validate the decision
        if decision != "end":
            valid_words = [word.lower() for word in unrevealed_words]
            if decision not in valid_words:
                # Try to match with valid words
                for word in valid_words:
                    if word in decision or decision in word:
                        decision = word
                        break
                else:
                    # If no match found, default to random
                    decision = random.choice(valid_words)
        
        # Log the decision
        self.decisions.append({
            "type": "guess",
            "prompt": prompt,
            "response": response_text,
            "parsed": {
                "reasoning": reasoning,
                "decision": decision
            }
        })
        
        return decision, reasoning

    def debate_response(self, debate_history: List[Dict], game_state: GameState, 
                        clue: str, number: int) -> str:
        """Generate a response in a debate about what word to guess"""
        unrevealed_words = [card.word for card in game_state.board if not card.revealed]
        
        # Format the debate history
        debate_text = ""
        for entry in debate_history:
            agent_name = entry.get("agent", "Unknown Agent")
            message = entry.get("message", "")
            debate_text += f"{agent_name}: {message}\n\n"
        
        prompt = f"""
You are {self.name}, a {self.team.value} team Operative in a game of Codenames participating in a team debate.

The Spymaster gave the clue: "{clue}" for {number} words.

The unrevealed words on the board are: {', '.join(unrevealed_words)}

DEBATE HISTORY:
{debate_text}

Now it's your turn to contribute to the debate. Consider what other team members have said.
You should either:
1. Argue for a specific word you think matches the clue
2. Express your concerns about words suggested by others
3. Show agreement with another team member's suggestion
4. Suggest ending the turn if you think it's the safest option

Give your perspective and reasoning. Don't just repeat what others have said.
"""
        
        response = self.make_api_call(
            f"You are {self.name}, a debating Codenames Operative. Be insightful but concise.", 
            prompt
        )
        
        # Log the debate contribution
        self.decisions.append({
            "type": "debate",
            "prompt": prompt,
            "response": response
        })
        
        return response

    def final_vote(self, debate_history: List[Dict], options: List[str], 
                   game_state: GameState, clue: str, number: int) -> str:
        """Cast a final vote after a debate"""
        unrevealed_words = [card.word for card in game_state.board if not card.revealed]
        
        # Format the debate history
        debate_text = ""
        for entry in debate_history:
            agent_name = entry.get("agent", "Unknown Agent")
            message = entry.get("message", "")
            debate_text += f"{agent_name}: {message}\n\n"
        
        # Format voting options
        options_text = "\n".join([f"- {option}" for option in options])
        
        prompt = f"""
You are {self.name}, a {self.team.value} team Operative in a game of Codenames.

After a team debate about the clue "{clue}" for {number} words, you must now cast your final vote.

The unrevealed words on the board are: {', '.join(unrevealed_words)}

DEBATE SUMMARY:
{debate_text}

VOTING OPTIONS:
{options_text}

Based on the debate and your own analysis, which option do you vote for?
Respond with EXACTLY one of the options listed above, nothing more.
"""
        
        response = self.make_api_call(
            f"You are {self.name}, voting on a Codenames guess. Be decisive.", 
            prompt
        )
        
        # Clean up response to match an option
        vote = response.strip().lower()
        
        # Try to match with available options
        best_option = None
        for option in options:
            if option.lower() == vote:
                best_option = option
                break
            elif option.lower() in vote:
                best_option = option
        
        # If no match, pick the first mentioned option in the response
        if not best_option:
            for option in options:
                if option.lower() in vote:
                    best_option = option
                    break
        
        # Fallback to random choice if still no match
        if not best_option and options:
            best_option = random.choice(options)
        
        # Log the vote
        self.decisions.append({
            "type": "vote",
            "prompt": prompt,
            "response": response,
            "parsed": {
                "vote": best_option
            }
        })
        
        return best_option 
