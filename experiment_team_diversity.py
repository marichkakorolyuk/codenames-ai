import os
import time
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
import random
import os

# Import the game function
from updated_play_codenames_game_standalone import play_codenames_game, CardType

class TeamDiversityExperiment:
    """Class to run Codenames experiments with varying model strengths and team sizes"""

    def __init__(self, 
                 red_models: List[str],
                 blue_models: List[str],
                 judge_model: str,
                 num_games: int,
                 max_turns: int,
                 seed: Optional[int] = None,
                 out_filename: str = "team_diversity_results.csv"):
        """
        Initialize the experiment runner
        
        Args:
            red_models: List of model identifiers for the red team. Length determines team size. Assumes all use the first model listed.
            blue_models: List of model identifiers for the blue team. Length determines team size. Assumes all use the first model listed.
            judge_model: Model identifier for the judge
            num_games: Number of games to run for this configuration
            max_turns: Maximum number of turns per game
            seed: Random seed for reproducibility (None for random)
            out_filename: Name of the CSV file to save results
        """
        if not red_models:
            raise ValueError("red_models list cannot be empty.")
        if not blue_models:
            raise ValueError("blue_models list cannot be empty.")
            
        self.red_models = red_models
        self.blue_models = blue_models
        self.red_team_size = len(red_models)
        self.blue_team_size = len(blue_models)
        self.judge_model = judge_model
        self.num_games = num_games
        self.max_turns = max_turns
        self.seed = seed
        self.results_df = None
        self.out_filename = out_filename
        self.timestamp = "" # Initialize timestamp

    def run_experiments(self) -> Optional[pd.DataFrame]:
        """
        Run experiments for the specified team configuration, recording the results
        
        Returns:
            DataFrame containing the experiment results for this run, or None if errors occurred.
        """
        # Initialize empty list to store experiment results for this run
        results = []
        
        # Create timestamp for this experiment run
        self.timestamp = time.strftime("%Y%m%d-%H%M%S")
        
        # Calculate total number of games to run for this instance
        total_games = self.num_games
        games_completed = 0
        
        # Represent model lists as strings for printing/logging
        red_models_str = ", ".join(self.red_models)
        blue_models_str = ", ".join(self.blue_models)

        print(f"\n=== Starting Codenames Team Diversity Experiment ===")
        print(f"Red Team: Size={self.red_team_size}, Models=[{red_models_str}]")
        print(f"Blue Team: Size={self.blue_team_size}, Models=[{blue_models_str}]")
        print(f"Judge model: {self.judge_model}")
        print(f"Total games to run in this session: {total_games}")
        
        # Create absolute path for the CSV file
        base_path = os.path.dirname(os.path.abspath(__file__))
        self.results_path = os.path.join(base_path, self.out_filename)
        print(f"Results will be appended to: {self.results_path}")
        
        # Check if the results file exists, create it with headers if not
        if not os.path.exists(self.results_path) or os.path.getsize(self.results_path) == 0:
            print(f"Creating new results file: {self.results_path}")
            # Define the columns for the results CSV
            columns = [
                'run_timestamp', 'game_num', 'red_team_size', 'red_models', 
                'blue_team_size', 'blue_models', 'judge_model', 'seed',
                'winner', 'red_team_won', 'blue_team_won', 'turns_played',
                'win_reason', 'game_duration'
            ]
            template_df = pd.DataFrame(columns=columns)
            template_df.to_csv(self.results_path, index=False)
            print(f"Created new results file with columns: {', '.join(columns)}")
        else:
            print(f"Appending to existing results file: {self.results_path}")
        
        # Record start time for the entire experiment run
        experiment_start_time = time.time()
        
        try:
            # Run the specified number of games
            for game_num in range(1, self.num_games + 1):
                try:
                    # Create a unique seed for this game if a base seed is provided
                    game_seed = None
                    if self.seed is not None:
                        # Simple way to generate a unique seed for each game in the run
                        game_seed = self.seed + game_num 
                    
                    print(f"  Running game {game_num}/{self.num_games} (Seed: {game_seed})...")
                    
                    # Start time for this specific game
                    game_start_time = time.time()
                    
                    # Run the game
                    game_state, game_outcome = play_codenames_game(
                        team_red_size=self.red_team_size,
                        team_blue_size=self.blue_team_size,
                        max_turns=self.max_turns,
                        seed=game_seed,
                        red_models=self.red_models,
                        blue_models=self.blue_models,
                        judge_model=self.judge_model
                    )
                    
                    # Calculate game duration (using duration from game_outcome if available)
                    game_duration = game_outcome.get('game_duration_seconds', time.time() - game_start_time)
                    
                    # Determine winner and win flags
                    winner = game_outcome.get('winner')
                    red_team_won = (winner == 'RED') if winner else False
                    blue_team_won = (winner == 'BLUE') if winner else False
                    
                    # Record the results
                    result = {
                        'run_timestamp': self.timestamp,
                        'game_num': game_num,
                        'red_team_size': self.red_team_size,
                        'red_models': ",".join(self.red_models),
                        'blue_team_size': self.blue_team_size,
                        'blue_models': ",".join(self.blue_models),
                        'judge_model': self.judge_model,
                        'seed': game_seed, # Record the actual seed used
                        'winner': winner,
                        'red_team_won': 1 if red_team_won else 0,
                        'blue_team_won': 1 if blue_team_won else 0,
                        'turns_played': game_outcome.get('turns_played'),
                        'win_reason': game_outcome.get('win_reason'),
                        'game_duration': game_duration
                    }
                    
                    results.append(result)
                    
                    # Create a temporary dataframe with the new result
                    temp_df = pd.DataFrame([result])
                    
                    # Append this result to the results file
                    try:
                        # Ensure columns match the file header order
                        if os.path.exists(self.results_path):
                            existing_cols = pd.read_csv(self.results_path, nrows=0).columns.tolist()
                            temp_df = temp_df[existing_cols] # Reorder columns to match file
                            
                        temp_df.to_csv(self.results_path, mode='a', header=False, index=False)
                        print(f"  Appended result to: {self.results_path}")
                    except Exception as e:
                        print(f"Error appending to results file: {e}. Trying without column matching.")
                        # Fallback: append raw dict if column matching fails
                        pd.DataFrame([result]).to_csv(self.results_path, mode='a', header=False, index=False)


                    # Update progress
                    games_completed += 1
                    progress_percent = (games_completed / total_games) * 100 if total_games > 0 else 0
                    print(f"  Game completed: {games_completed}/{total_games} ({progress_percent:.1f}%)")
                    
                except Exception as e:
                    print(f"Error during game execution (Game {game_num}): {e}")
                    import traceback
                    traceback.print_exc()
                    # Optionally add a placeholder result indicating failure
                    # results.append({ 'run_timestamp': self.timestamp, 'game_num': game_num, 'error': str(e), ... })
                            
        except Exception as e:
            print(f"Exception during experiment setup or loop: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # Create the final dataframe with all results from this specific run
            if results:
                self.results_df = pd.DataFrame(results)
                
                # Print summary of results for this run
                self._print_run_summary()
                
                # Attempt to print summary of all combined results from the file
                self._print_combined_summary()
                
            else:
                print("No games were successfully completed in this run.")
                self.results_df = pd.DataFrame() # Ensure results_df is a DataFrame

            run_duration = time.time() - experiment_start_time
            print(f"Experiment run completed in {run_duration:.2f} seconds")
            return self.results_df # Return results from this run
    
    def _print_run_summary(self):
        """Print a summary of the results from the current experiment run"""
        if self.results_df is None or self.results_df.empty:
            print("No results from this run to summarize.")
            return
        
        print("\n=== Summary for Current Run ===")
        
        # Represent model lists as strings for printing/logging
        red_models_str = ", ".join(self.red_models)
        blue_models_str = ", ".join(self.blue_models)

        total_games_run = len(self.results_df)
        red_wins = self.results_df['red_team_won'].sum()
        blue_wins = self.results_df['blue_team_won'].sum()
        avg_turns = self.results_df['turns_played'].mean()
        avg_duration = self.results_df['game_duration'].mean()

        print(f"Configuration: Red (Size={self.red_team_size}, Models=[{red_models_str}]) vs Blue (Size={self.blue_team_size}, Models=[{blue_models_str}])")
        print(f"Judge: {self.judge_model}")
        print(f"Games completed in this run: {total_games_run}")
        print(f"Red Team Win Rate: { (red_wins / total_games_run * 100) if total_games_run else 0:.1f}% ({red_wins} wins)")
        print(f"Blue Team Win Rate: { (blue_wins / total_games_run * 100) if total_games_run else 0:.1f}% ({blue_wins} wins)")
        print(f"Average Turns: {avg_turns:.1f}")
        print(f"Average Game Duration: {avg_duration:.2f} seconds")


    def _print_combined_summary(self):
        """Print a summary of all results in the CSV file"""
        print("=== Summary of All Experiments in File ===")
        try:
            # Read with more flexible error handling and potential column mismatches
            all_results_df = pd.read_csv(self.results_path, on_bad_lines='warn')
            
            if all_results_df.empty:
                 print("Results file is empty or could not be read properly.")
                 return

            # Ensure necessary columns exist, fill with NaN if not
            required_cols = ['red_team_size', 'red_models', 'blue_team_size', 'blue_models', 
                             'red_team_won', 'blue_team_won', 'turns_played', 'game_duration']
            for col in required_cols:
                if col not in all_results_df.columns:
                    all_results_df[col] = np.nan # Use NaN for missing numeric data
            
            # Group by the team configurations
            summary = all_results_df.groupby(['red_team_size', 'red_models', 'blue_team_size', 'blue_models']).agg(
                games_played=('run_timestamp', 'count'), # Count any non-null column like timestamp
                red_win_rate=('red_team_won', 'mean'),
                blue_win_rate=('blue_team_won', 'mean'),
                avg_turns=('turns_played', 'mean'),
                avg_duration=('game_duration', 'mean')
            ).reset_index()
            
            # Format win rates as percentages
            summary['red_win_rate'] = (summary['red_win_rate'] * 100).round(1)
            summary['blue_win_rate'] = (summary['blue_win_rate'] * 100).round(1)
            summary['avg_turns'] = summary['avg_turns'].round(1)
            summary['avg_duration'] = summary['avg_duration'].round(2)
            
            # Rename columns for clarity
            summary.rename(columns={
                'red_team_size': 'Red Size', 'red_models': 'Red Models',
                'blue_team_size': 'Blue Size', 'blue_models': 'Blue Models',
                'games_played': 'Games', 'red_win_rate': 'Red Win %',
                'blue_win_rate': 'Blue Win %', 'avg_turns': 'Avg Turns',
                'avg_duration': 'Avg Duration (s)'
            }, inplace=True)

            print(summary.to_string(index=False)) # Print full summary table
            print(f"Total games in combined results file: {len(all_results_df)}")
            
        except FileNotFoundError:
            print(f"Results file not found: {self.results_path}")
        except pd.errors.EmptyDataError:
             print(f"Results file is empty: {self.results_path}")
        except Exception as e:
            print(f"Error analyzing combined results: {e}")
            import traceback
            traceback.print_exc()

# def run_model_strength_experiment(
#     weaker_model: str = "anthropic/claude-3-sonnet",
#     stronger_model: str = "anthropic/claude-3.7-sonnet",
#     judge_model: str = "anthropic/claude-3.7-sonnet",
#     weaker_team_min: int = 2,
#     weaker_team_max: int = 5,
#     weaker_team_step: int = 1,
#     stronger_team_size: int = 2,
#     iterations: int = 1,
#     max_turns: int = 20,
#     weaker_team_color: str = "RED",
#     seed: int = None
# ):
#     """
#     Run an experiment comparing different model strengths with varying team sizes
    
#     Args:
#         weaker_model: The weaker model identifier
#         stronger_model: The stronger model identifier
#         judge_model: The model to use for judging debates
#         weaker_team_min: Minimum size for the weaker team
#         weaker_team_max: Maximum size for the weaker team
#         weaker_team_step: Step size for increasing weaker team
#         stronger_team_size: Fixed size for the stronger team
#         iterations: Number of games to run per configuration
#         max_turns: Maximum number of turns per game
#         weaker_team_color: Which team color to assign to the weaker model ("RED" or "BLUE")
#         seed: Random seed for reproducibility (None for random)
    
#     Returns:
#         The experiment object containing the results
#     """
#     # Generate weaker team sizes
#     weaker_team_sizes = list(range(weaker_team_min, weaker_team_max + 1, weaker_team_step))
    
#     # Create and run the experiment
#     experiment = ModelStrengthExperiment(
#         weaker_team_sizes=weaker_team_sizes,
#         stronger_team_sizes=[stronger_team_size],
#         weaker_model=weaker_model,
#         stronger_model=stronger_model,
#         judge_model=judge_model,
#         iterations=iterations,
#         max_turns=max_turns,
#         weaker_team_color=weaker_team_color,
#         seed=seed
#     )
    
#     # Run the experiments
#     experiment.run_experiments()
    
#     return experiment


# if __name__ == "__main__":
#     # Run a test experiment with 1 iteration
#     # RED team uses weaker model (claude-3-sonnet)
#     # BLUE team uses stronger model (claude-3.7-sonnet)
#     experiment = run_model_strength_experiment(
#         weaker_model="anthropic/claude-3-sonnet",  # Weaker model
#         stronger_model="anthropic/claude-3.7-sonnet",  # Stronger model
#         judge_model="anthropic/claude-3.7-sonnet",  # Judge model (smartest)
#         weaker_team_min=2,  # Start with 2 agents on the weaker team
#         weaker_team_max=3,  # Test up to 3 agents on the weaker team
#         weaker_team_step=1,  # Increase by 1
#         stronger_team_size=2,  # Fixed 2 agents on the stronger team
#         iterations=5,  # Just 1 iteration for testing
#         weaker_team_color="RED"  # Assign the weaker model to RED team
#     )

# Example of how to potentially use the updated class (replace the old main block)
if __name__ == "__main__":
    # Example configuration: 2 vs 3 game with diverse models on blue team
    experiment = TeamDiversityExperiment(
        red_models=["anthropic/claude-3-haiku", "anthropic/claude-3-haiku"],  # Red team: 2 Haiku models
        blue_models=["anthropic/claude-3-sonnet", "anthropic/claude-3-opus", "anthropic/claude-3-sonnet"], # Blue team: 2 Sonnet, 1 Opus
        judge_model="anthropic/claude-3-opus",      # Judge model
        num_games=5,                                 # Run 5 games for this config
        max_turns=20,
        seed=42,                                     # Optional seed
        out_filename="team_diversity_test_results.csv" # Specific output file
    )
    
    # Run the experiments
    results_df = experiment.run_experiments()
    
    # You can access the results dataframe if needed
    # if results_df is not None:
    #    print("DataFrame from the last run:")
    #    print(results_df)

    # Example configuration: 3 vs 3 game, different models
    # experiment_2 = TeamDiversityExperiment(
    #     red_models=["anthropic/claude-3-sonnet"] * 3, # Team of 3 Sonnets
    #     blue_models=["anthropic/claude-3-haiku"] * 3, # Team of 3 Haikus
    #     judge_model="anthropic/claude-3-opus",
    #     num_games=3,                                
    #     max_turns=20,
    #     seed=123,                                    
    #     out_filename="team_diversity_test_results.csv" # Append to the same file
    # )
    # experiment_2.run_experiments()
