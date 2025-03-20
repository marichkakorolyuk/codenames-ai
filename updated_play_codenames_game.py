# Global variables for SimpleOperativeAgent to reference
unrevealed_words = []
revealed_words = []

import time

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
        A tuple containing (game_state, game_outcome)
        where game_outcome is a dictionary with details about the game results
    """
    # Start tracking game time
    start_time = time.time()
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
        
        # Use the DebateJudge to determine agreed upon words
        debate_judge_prompt = f"""
You are participating in a team debate for Codenames Judge.
You are given responses from operatives affiliated with team {current_team}
Spymaster has given the clue '{clue_word}' {clue_n_words}.

debate_history={debate_history}

You must return two lists: guesses where operatives agree, and where they disagree. List with words where operatives agree should be sorted by level of their agreement and confidence.

IMPORTANT: Only consider words from this list: {unrevealed_words}
"""
        
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
            # Create empty list for selected cards initially
            # This starts the clue process without making any guesses yet
            selected_cards = []
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
            print(game_state)
            
        except ValueError as e:
            print(f"Error processing clue: {e}")
    
    # Track win reason and prepare detailed outcome information
    end_time = time.time()
    game_duration = end_time - start_time
    
    # Estimate tokens used based on the number of turns and team sizes
    # For each turn, we have:
    # - 1 spymaster prompt (input) and response (output) for the active team
    # - N operative prompts (input) and responses (output) where N is the team size
    # - 1 debate judge prompt (input) and response (output)
    # Average token counts per interaction (estimated):
    avg_spymaster_input_tokens = 1000  # Tokens for prompt to spymaster
    avg_spymaster_output_tokens = 300   # Tokens for spymaster's response
    avg_operative_input_tokens = 1200   # Tokens for prompt to operatives (includes clue and debate history)
    avg_operative_output_tokens = 400    # Tokens for operative's response
    avg_judge_input_tokens = 1500       # Tokens for prompt to debate judge (includes all operative responses)
    avg_judge_output_tokens = 200        # Tokens for judge's decision
    
    # Calculate total tokens by turn
    total_input_tokens = 0
    total_output_tokens = 0
    
    # Iterate through each turn and calculate tokens based on which team was active
    for turn_index in range(turn_count):
        # Determine which team was active in this turn (alternating)
        if turn_index % 2 == 0:  # Even turns (0-indexed) are BLUE team's turns
            active_team_size = team_blue_size
        else:  # Odd turns are RED team's turns
            active_team_size = team_red_size
            
        # Add tokens for this turn
        total_input_tokens += avg_spymaster_input_tokens + (active_team_size * avg_operative_input_tokens) + avg_judge_input_tokens
        total_output_tokens += avg_spymaster_output_tokens + (active_team_size * avg_operative_output_tokens) + avg_judge_output_tokens
    
    game_outcome = {
        "turns_played": turn_count,
        "winner": None,
        "win_reason": None,
        "game_duration_seconds": game_duration,
        "total_input_tokens": total_input_tokens,
        "total_output_tokens": total_output_tokens,
        "total_tokens": total_input_tokens + total_output_tokens
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
        print(f"Estimated tokens used: {game_outcome['total_tokens']:,} (Input: {game_outcome['total_input_tokens']:,}, Output: {game_outcome['total_output_tokens']:,})")
    else:
        game_outcome["win_reason"] = "Game ended due to maximum turn limit"
        print("\nGame ended due to maximum turn limit")
        print(f"Game played for maximum {turn_count} turns")
        print(f"Game duration: {game_duration:.2f} seconds")
        print(f"Estimated tokens used: {game_outcome['total_tokens']:,} (Input: {game_outcome['total_input_tokens']:,}, Output: {game_outcome['total_output_tokens']:,})")
    
    # Return both the game state and detailed outcome information
    return game_state, game_outcome
