from openai import OpenAI
from codenames.game import CardType

class UpdatedOperativeAgent:
    """
    A simple agent that uses OpenAI to simulate an operative player.
    This version includes the ability to receive the list of available words.
    """
    def __init__(self, team: CardType, name: str = None):
        """
        Initialize a new operative agent.
        
        Args:
            team: The team this agent belongs to
            name: Optional name for the agent
        """
        self.team = team
        self.name = name or f"Operative {team.value}"
    
    def generate(self, clue_word, clue_n_words, debate_history="", max_completion_tokens=150, available_words=None):
        """
        Generate reasoning for a given clue.
        
        Args:
            clue_word: The clue word given by the spymaster
            clue_n_words: The number associated with the clue
            debate_history: Optional history of previous debate turns
            max_completion_tokens: Maximum number of tokens for the response
            available_words: List of words that are currently available on the board
            
        Returns:
            The reasoning for the operative's guess
        """
        prompt = f"""
You are participating in a team debate for Codenames as the {self.team.value} Operative. Your name is {self.name}
Your Spymaster has given the clue '{clue_word}' {clue_n_words}.

{f'These are the available words on the board: {available_words}' if available_words else ''}

Your task is to debate with your team on what words you think the Spymaster is hinting at. You should consider the semantic relatedness of words to the clue.

{f'Previous debate turns: {debate_history}' if debate_history else ''}

Remember, this is a collaborative game - you should try to reach a consensus with the other operatives.

IMPORTANT: ONLY discuss words from the available words list that you've been given!

You MUST keep your response under {max_completion_tokens} words. Your response should include reasoning and your best guess.
"""
        client = OpenAI()
        completion = client.chat.completions.create(
            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "user", "content": prompt},
            ],
            max_tokens=max_completion_tokens
        )
        
        response = completion.choices[0].message
        return response.content
