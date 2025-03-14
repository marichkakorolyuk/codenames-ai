"""
Decision Mechanisms for AI Codenames
Contains debate, voting, and consensus mechanisms for multi-agent decision making
"""

import random
from typing import Dict, List, Tuple, Any, Optional
from collections import Counter
from game_core import GameState
import ai_agents

class DebateManager:
    """Manages debates between multiple agents"""
    def __init__(self, max_rounds: int = 3):
        self.max_rounds = max_rounds
    
    def run_debate(self, agents: List[ai_agents.OperativeAgent], game_state: GameState, 
                  clue: str, number: int, correct_guesses: int, 
                  previous_guesses: List[Dict]) -> Dict[str, Any]:
        """Run a multi-round debate between agents to decide on a guess
        
        Returns:
            Dict containing debate_log, final_decision, vote_counts, and reasoning
        """
        # Initial proposals
        debate_log = []
        print(f"\n===== STARTING TEAM DEBATE ABOUT CLUE: '{clue}' {number} =====")
        
        # First round: Each agent proposes a guess with reasoning
        print("\n--- ROUND 1: INITIAL PROPOSALS ---")
        proposals = {}
        for agent in agents:
            guess, reasoning = agent.generate_guess(
                game_state, clue, number, correct_guesses, previous_guesses
            )
            
            proposals[agent.name] = {
                "guess": guess,
                "reasoning": reasoning
            }
            
            message = f"I suggest we guess '{guess}'.\nMy reasoning: {reasoning}"
            debate_log.append({
                "round": 1,
                "agent": agent.name,
                "message": message,
                "guess": guess
            })
            
            print(f"{agent.name} proposes: {guess}")
            print(f"Reasoning: {reasoning[:100]}..." if len(reasoning) > 100 else f"Reasoning: {reasoning}")
            print()
        
        # Additional debate rounds
        for round_num in range(2, self.max_rounds + 1):
            print(f"\n--- ROUND {round_num}: DISCUSSION ---")
            
            for agent in agents:
                # Agent responds to the ongoing debate
                response = agent.debate_response(debate_log, game_state, clue, number)
                
                # Try to extract a current preference from the response
                current_guess = self._extract_preference(response, game_state)
                
                debate_log.append({
                    "round": round_num,
                    "agent": agent.name,
                    "message": response,
                    "guess": current_guess
                })
                
                print(f"{agent.name}: {response[:150]}..." if len(response) > 150 else f"{agent.name}: {response}")
                if current_guess:
                    print(f"Current preference: {current_guess}")
                print()
        
        # Final voting round
        print("\n--- FINAL VOTING ROUND ---")
        
        # Collect all unique proposed guesses (including "end")
        all_guesses = set()
        for entry in debate_log:
            if entry.get("guess"):
                all_guesses.add(entry.get("guess"))
        
        # Ensure "end" is always an option
        all_guesses.add("end")
        
        # Convert to list and sort for consistency
        voting_options = sorted(list(all_guesses))
        print(f"Voting options: {', '.join(voting_options)}")
        
        # Each agent casts a final vote
        votes = {}
        for agent in agents:
            vote = agent.final_vote(debate_log, voting_options, game_state, clue, number)
            votes[agent.name] = vote
            print(f"{agent.name} votes for: {vote}")
        
        # Count votes
        vote_counter = Counter(votes.values())
        top_votes = vote_counter.most_common()
        
        # If there's a tie, break it randomly
        if len(top_votes) > 1 and top_votes[0][1] == top_votes[1][1]:
            tied_options = [option for option, count in top_votes if count == top_votes[0][1]]
            final_decision = random.choice(tied_options)
            print(f"\nTIE BREAKER: Randomly selected '{final_decision}' from tied options: {tied_options}")
        else:
            final_decision = top_votes[0][0]
        
        print(f"\nFINAL DECISION: {final_decision} (with {vote_counter[final_decision]} out of {len(agents)} votes)")
        
        # Collect reasoning for the final decision
        final_reasoning = []
        for entry in debate_log:
            if entry.get("guess") == final_decision:
                final_reasoning.append(f"{entry['agent']}: {entry['message']}")
        
        result = {
            "debate_log": debate_log,
            "final_decision": final_decision,
            "vote_counts": dict(vote_counter),
            "reasoning": final_reasoning[:2] if final_reasoning else ["No specific reasoning provided"]
        }
        
        return result
    
    def _extract_preference(self, message: str, game_state: str) -> Optional[str]:
        """Try to extract the current word preference from a debate message"""
        message = message.lower()
        
        # Check for explicit "end turn" mentions
        if ("end turn" in message or "end the turn" in message or 
            "ending the turn" in message or "ending our turn" in message):
            return "end"
        
        # Check for board words
        unrevealed_words = [card.word.lower() for card in game_state.board if not card.revealed]
        
        # Check for quotes which might indicate a word preference
        import re
        quoted = re.findall(r"'([^']*)'|\"([^\"]*)\"", message)
        for match in quoted:
            for potential in match:
                if potential.lower() in unrevealed_words:
                    return potential.lower()
        
        # Look for direct mentions of board words
        for word in unrevealed_words:
            # Check if word is mentioned as a standalone term
            word_pattern = r'\b' + re.escape(word) + r'\b'
            if re.search(word_pattern, message, re.IGNORECASE):
                return word
        
        # If we can't confidently extract a preference, return None
        return None 
