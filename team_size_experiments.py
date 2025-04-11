import csv
import os
import time
import random

from updated_play_codenames_game_standalone import play_codenames_game
import dotenv
dotenv.load_dotenv()
def run_simple_experiment(
    red_team_min,
    red_team_max,
    red_team_step,
    blue_team_min,
    blue_team_max,
    blue_team_step,
    iterations,
    max_turns,
    output_file="team_size_results.csv"
):
    """
    A simple function to run Codenames experiments with different team sizes.
    
    Args:
        red_team_min: Minimum number of red team members
        red_team_max: Maximum number of red team members
        red_team_step: Step size for increasing red team
        blue_team_min: Minimum number of blue team members
        blue_team_max: Maximum number of blue team members
        blue_team_step: Step size for increasing blue team
        iterations: Number of games to run per configuration
        max_turns: Maximum turns per game
        output_file: File to save results
    """
    # Create the output file or append to existing one
    file_exists = os.path.isfile(output_file)
    
    with open(output_file, 'a', newline='') as csvfile:
        fieldnames = [
            'red_team_size', 'blue_team_size', 'team_size_difference', 
            'iteration', 'winner', 'red_win', 'blue_win', 'turns_played', 
            'win_reason', 'game_duration'
        ]
        
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        # Write header if file doesn't exist
        if not file_exists:
            writer.writeheader()
        
        # Calculate total games to run
        red_sizes = range(red_team_min, red_team_max + 1, red_team_step)
        blue_sizes = range(blue_team_min, blue_team_max + 1, blue_team_step)
        total_games = len(red_sizes) * len(blue_sizes) * iterations
        games_completed = 0
        
        print(f"Starting experiment with {total_games} total games to run")
        
        # Simple nested loops to run all combinations
        for red_team_size in red_sizes:
            for blue_team_size in blue_sizes:
                for iteration in range(1, iterations + 1):
                    # Generate a random seed for reproducibility
                    game_seed = random.randint(1, 1000000)
                    
                    print(f"\nRunning game: Red={red_team_size}, Blue={blue_team_size}, Iteration={iteration}")
                    
                    try:
                        # Run a single game
                        game_state, game_outcome = play_codenames_game(
                            team_red_size=red_team_size,
                            team_blue_size=blue_team_size,
                            max_turns=max_turns,
                            seed=game_seed
                        )
                        
                        # Prepare the result row
                        result = {
                            'red_team_size': red_team_size,
                            'blue_team_size': blue_team_size,
                            'team_size_difference': blue_team_size - red_team_size,
                            'iteration': iteration,
                            'winner': game_outcome['winner'] if game_outcome['winner'] else '',
                            'red_win': 1 if game_outcome['winner'] == 'RED' else 0,
                            'blue_win': 1 if game_outcome['winner'] == 'BLUE' else 0,
                            'turns_played': game_outcome['turns_played'],
                            'win_reason': game_outcome['win_reason'],
                            'game_duration': game_outcome['game_duration_seconds']
                        }
                        
                        # Write to CSV immediately after each game
                        writer.writerow(result)
                        csvfile.flush()  # Make sure it's written to disk
                        
                        games_completed += 1
                        print(f"Game completed ({games_completed}/{total_games})")
                        print(f"Winner: {result['winner'] or 'None'}")
                        print(f"Reason: {result['win_reason']}")
                        
                    except Exception as e:
                        print(f"Error running game: {e}")
                        # Write error to file to keep track of issues
                        with open("experiment_errors.log", "a") as error_file:
                            error_file.write(f"Error in game Red={red_team_size}, Blue={blue_team_size}, Iteration={iteration}: {str(e)}\n")
        
        print(f"\nExperiment completed. Results saved to {output_file}")

if __name__ == "__main__":
    # Using the parameters you specified
    run_simple_experiment(
        red_team_min=2,
        red_team_max=2,
        red_team_step=2,
        blue_team_min=2,
        blue_team_max=10,
        blue_team_step=2,
        iterations=1,
        max_turns=20,
        output_file="team_size_results.csv"
    )