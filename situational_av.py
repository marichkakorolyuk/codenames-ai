#!/usr/bin/env python
import csv
from updated_play_codenames_game_standalone import play_codenames_game

# Simple function to run games and track results
def run_games(num_games=10):
    # Track wins for each team
    red_wins = 0
    blue_wins = 0
    

    # Run games
    for i in range(1, num_games + 1):
        print(f"\nRunning game {i}/{num_games}")
        
        # Use requested parameters
        game_result = play_codenames_game(
            team_red_size=4, 
            team_blue_size=4, 
            max_turns=20, 
            seed=None, 
            debate_rounds=1, 
            red_model="anthropic/claude-3.7-sonnet:thinking",
            blue_model="anthropic/claude-3.7-sonnet:thinking",
            judge_model="openai/gpt-4.1",
            red_models=None, 
            blue_models=None,
            setup_logging_file=True
        )
        
        # Unpack the tuple - play_codenames_game returns (game_state, game_outcome)
        _, game_outcome = game_result
        
        # Extract data from game_outcome
        winner = game_outcome.get('winner')
        turn_count = game_outcome.get('turns_played', 0)
        win_reason = game_outcome.get('win_reason')
        
        # Track winner
        if winner == 'RED':
            red_wins += 1
        elif winner == 'BLUE':
            blue_wins += 1
            
        print(f"Game {i} complete. Winner: {winner}")
        
        # Print current standings
        print(f"Current standings: RED {red_wins} - BLUE {blue_wins}")
        
        # Write result to CSV
        with open('situational_results.csv', 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([i, winner, turn_count, win_reason])
    
    # Print final results
    print("\n===== FINAL RESULTS =====")
    print(f"RED wins: {red_wins}/{num_games} ({red_wins/num_games*100:.1f}%)")
    print(f"BLUE wins: {blue_wins}/{num_games} ({blue_wins/num_games*100:.1f}%)")

# Run 10 games
if __name__ == "__main__":
    run_games(5)

