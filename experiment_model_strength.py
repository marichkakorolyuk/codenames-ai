import os
import time
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple
import random

# Import the game function
from updated_play_codenames_game_standalone import play_codenames_game, CardType

class ModelStrengthExperiment:
    """Class to run Codenames experiments with varying model strengths and team sizes"""

    def __init__(self, 
                 weaker_team_sizes: List[int],
                 stronger_team_sizes: List[int],
                 weaker_model: str,
                 stronger_model: str,
                 judge_model: str,
                 iterations: int,
                 max_turns: int,
                 weaker_team_color: str = "RED",
                 seed: int = None):
        """
        Initialize the experiment runner
        
        Args:
            weaker_team_sizes: List of team sizes to test for the weaker model team
            stronger_team_sizes: List of team sizes to test for the stronger model team
            weaker_model: Model identifier for the weaker model
            stronger_model: Model identifier for the stronger model
            judge_model: Model identifier for the judge
            iterations: Number of games to run per configuration
            max_turns: Maximum number of turns per game
            weaker_team_color: Which team color to assign to the weaker model ("RED" or "BLUE")
            seed: Random seed for reproducibility (None for random)
        """
        self.weaker_team_sizes = weaker_team_sizes
        self.stronger_team_sizes = stronger_team_sizes
        self.weaker_model = weaker_model
        self.stronger_model = stronger_model
        self.judge_model = judge_model
        self.iterations = iterations
        self.max_turns = max_turns
        self.weaker_team_color = weaker_team_color.upper()
        self.stronger_team_color = "BLUE" if self.weaker_team_color == "RED" else "RED"
        self.seed = seed
        self.results_df = None
        
    def run_experiments(self) -> pd.DataFrame:
        """
        Run experiments with various team sizes and model strengths, recording the results
        
        Returns:
            DataFrame containing the experiment results
        """
        # Initialize empty list to store experiment results
        results = []
        
        # Create timestamp for this experiment run
        self.timestamp = time.strftime("%Y%m%d-%H%M%S")
        
        # Calculate total number of games to run
        total_games = len(self.weaker_team_sizes) * len(self.stronger_team_sizes) * self.iterations
        games_completed = 0
        
        print(f"\n=== Starting Codenames Model Strength Experiments ===")
        print(f"{self.weaker_team_color} team (weaker model: {self.weaker_model}) sizes: {self.weaker_team_sizes}")
        print(f"{self.stronger_team_color} team (stronger model: {self.stronger_model}) sizes: {self.stronger_team_sizes}")
        print(f"Judge model: {self.judge_model}")
        print(f"Iterations per configuration: {self.iterations}")
        print(f"Total games to run: {total_games}")
        
        # Create absolute paths for CSV files
        import os
        base_path = os.path.dirname(os.path.abspath(__file__))
        
        # Define the results file path
        self.results_path = os.path.join(base_path, "model_strength_results.csv")
        print(f"Results will be appended to: {self.results_path}")
        
        # Check if the results file exists, create it with headers if not
        if not os.path.exists(self.results_path) or os.path.getsize(self.results_path) == 0:
            print(f"Creating new results file: {self.results_path}")
            # Create a template dataframe with all the expected columns
            columns = [
                'weaker_team_color', 'weaker_team_size', 'weaker_model',
                'stronger_team_color', 'stronger_team_size', 'stronger_model',
                'judge_model', 'team_size_ratio', 'iteration', 'winner',
                'weaker_team_won', 'stronger_team_won', 'turns_played',
                'win_reason', 'game_duration', 'red_team_size', 'red_model',
                'blue_team_size', 'blue_model'
            ]
            template_df = pd.DataFrame(columns=columns)
            template_df.to_csv(self.results_path, index=False)
            print(f"Created new results file with columns: {', '.join(columns)}")
        else:
            print(f"Appending to existing results file: {self.results_path}")
        
        # Record start time for the entire experiment
        experiment_start_time = time.time()
        
        try:
            # Run experiments for each team size combination
            for weaker_team_size in self.weaker_team_sizes:
                for stronger_team_size in self.stronger_team_sizes:
                    print(f"\nTesting with {self.weaker_team_color} team (weaker) size = {weaker_team_size}, "
                          f"{self.stronger_team_color} team (stronger) size = {stronger_team_size}")
                    
                    # Run multiple iterations for each configuration
                    for iteration in range(1, self.iterations + 1):
                        try:
                            # Create a unique seed for this game if a base seed is provided
                            game_seed = None
                            if self.seed is not None:
                                game_seed = self.seed + (weaker_team_size * 10000) + (stronger_team_size * 1000) + iteration
                            
                            print(f"  Running iteration {iteration}/{self.iterations}...")
                            
                            # Start time for this specific game
                            game_start_time = time.time()
                            
                            # Set up models based on team color
                            if self.weaker_team_color == "RED":
                                red_model = self.weaker_model
                                blue_model = self.stronger_model
                                red_team_size = weaker_team_size
                                blue_team_size = stronger_team_size
                            else:  # weaker team is BLUE
                                red_model = self.stronger_model
                                blue_model = self.weaker_model
                                red_team_size = stronger_team_size
                                blue_team_size = weaker_team_size
                            
                            # Run the game
                            game_state, game_outcome = play_codenames_game(
                                team_red_size=red_team_size,
                                team_blue_size=blue_team_size,
                                max_turns=self.max_turns,
                                seed=game_seed,
                                red_model=red_model,
                                blue_model=blue_model,
                                judge_model=self.judge_model
                            )
                            
                            # Calculate game duration
                            game_duration = time.time() - game_start_time
                            
                            # Determine if the weaker team won
                            winner = game_outcome['winner']
                            weaker_team_won = (winner == self.weaker_team_color) if winner else False
                            stronger_team_won = (winner == self.stronger_team_color) if winner else False
                            
                            # Record the results
                            result = {
                                'weaker_team_color': self.weaker_team_color,
                                'weaker_team_size': weaker_team_size,
                                'weaker_model': self.weaker_model,
                                'stronger_team_color': self.stronger_team_color,
                                'stronger_team_size': stronger_team_size,
                                'stronger_model': self.stronger_model,
                                'judge_model': self.judge_model,
                                'team_size_ratio': weaker_team_size / stronger_team_size,
                                'iteration': iteration,
                                'winner': winner,
                                'weaker_team_won': 1 if weaker_team_won else 0,
                                'stronger_team_won': 1 if stronger_team_won else 0,
                                'turns_played': game_outcome['turns_played'],
                                'win_reason': game_outcome['win_reason'],
                                'game_duration': game_outcome['game_duration_seconds'],
                                'red_team_size': red_team_size,
                                'red_model': red_model,
                                'blue_team_size': blue_team_size,
                                'blue_model': blue_model,
                            }
                            
                            results.append(result)
                            
                            # Create a temporary dataframe with the new result
                            temp_df = pd.DataFrame([result])
                            
                            # Append this result to the results file
                            try:
                                temp_df.to_csv(self.results_path, mode='a', header=False, index=False)
                                print(f"  Appended result to: {self.results_path}")
                            except Exception as e:
                                print(f"Error appending to results file: {e}")
                            
                            # Update progress
                            games_completed += 1
                            print(f"  Game completed: {games_completed}/{total_games} ({(games_completed/total_games)*100:.1f}%)")
                            
                        except Exception as e:
                            print(f"Error during game execution: {e}")
                            # Print traceback
                            import traceback
                            traceback.print_exc()
                            
        except Exception as e:
            print(f"Exception during experiment: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # Create the final dataframe with all results from this run
            if results:
                self.results_df = pd.DataFrame(results)
                
                # Print summary of results for this run
                self._print_summary()
                
                # Also print the combined results from all runs
                try:
                    # Read with more flexible error handling
                    all_results_df = pd.read_csv(self.results_path, on_bad_lines='warn')
                    
                    # Ensure we only use the columns we expect
                    expected_columns = [
                        'weaker_team_color', 'weaker_team_size', 'weaker_model',
                        'stronger_team_color', 'stronger_team_size', 'stronger_model',
                        'judge_model', 'team_size_ratio', 'iteration', 'winner',
                        'weaker_team_won', 'stronger_team_won', 'turns_played',
                        'win_reason', 'game_duration', 'red_team_size', 'red_model',
                        'blue_team_size', 'blue_model'
                    ]
                    
                    # Filter to only columns we need
                    for col in expected_columns:
                        if col not in all_results_df.columns:
                            all_results_df[col] = None
                    all_results_df = all_results_df[expected_columns]
                    
                    print("\n=== Summary of All Experiments ===")
                    summary = all_results_df.groupby(['weaker_team_size', 'stronger_team_size']).agg({
                        'weaker_team_won': ['mean', 'count'],
                        'stronger_team_won': ['mean'],
                        'turns_played': ['mean'],
                    }).reset_index()
                    
                    # Format column names for better readability
                    summary.columns = ['weaker_size', 'stronger_size', 'weaker_win_rate', 'games_played', 
                                      'stronger_win_rate', 'avg_turns']
                    
                    # Convert win rates to percentages
                    summary['weaker_win_rate'] = summary['weaker_win_rate'] * 100
                    summary['stronger_win_rate'] = summary['stronger_win_rate'] * 100
                    
                    print(summary)
                    print(f"\nTotal games in combined results: {len(all_results_df)}")
                    
                except Exception as e:
                    print(f"Error analyzing combined results: {e}")
                
            print(f"\nExperiment completed in {time.time() - experiment_start_time:.2f} seconds")
            return self.results_df
    
    def _print_summary(self):
        """Print a summary of the experiment results"""
        if self.results_df is None or len(self.results_df) == 0:
            print("No results to summarize")
            return
        
        print("\n=== Experiment Summary ===")
        
        # Group by team sizes and calculate win rates
        summary = self.results_df.groupby(['weaker_team_size', 'stronger_team_size']).agg({
            'weaker_team_won': 'mean',
            'stronger_team_won': 'mean',
            'turns_played': 'mean',
            'game_duration': 'mean'
        }).reset_index()
        
        # Format win rates as percentages
        summary['weaker_win_rate'] = summary['weaker_team_won'] * 100
        summary['stronger_win_rate'] = summary['stronger_team_won'] * 100
        
        # Print the summary
        print(summary[['weaker_team_size', 'stronger_team_size', 'weaker_win_rate', 'stronger_win_rate', 'turns_played', 'game_duration']])
        print("\nFull results saved to:", "model_strength_results.csv")


def run_model_strength_experiment(
    weaker_model: str = "anthropic/claude-3-sonnet",
    stronger_model: str = "anthropic/claude-3.7-sonnet",
    judge_model: str = "anthropic/claude-3.7-sonnet",
    weaker_team_min: int = 2,
    weaker_team_max: int = 5,
    weaker_team_step: int = 1,
    stronger_team_size: int = 2,
    iterations: int = 1,
    max_turns: int = 20,
    weaker_team_color: str = "RED",
    seed: int = None
):
    """
    Run an experiment comparing different model strengths with varying team sizes
    
    Args:
        weaker_model: The weaker model identifier
        stronger_model: The stronger model identifier
        judge_model: The model to use for judging debates
        weaker_team_min: Minimum size for the weaker team
        weaker_team_max: Maximum size for the weaker team
        weaker_team_step: Step size for increasing weaker team
        stronger_team_size: Fixed size for the stronger team
        iterations: Number of games to run per configuration
        max_turns: Maximum number of turns per game
        weaker_team_color: Which team color to assign to the weaker model ("RED" or "BLUE")
        seed: Random seed for reproducibility (None for random)
    
    Returns:
        The experiment object containing the results
    """
    # Generate weaker team sizes
    weaker_team_sizes = list(range(weaker_team_min, weaker_team_max + 1, weaker_team_step))
    
    # Create and run the experiment
    experiment = ModelStrengthExperiment(
        weaker_team_sizes=weaker_team_sizes,
        stronger_team_sizes=[stronger_team_size],
        weaker_model=weaker_model,
        stronger_model=stronger_model,
        judge_model=judge_model,
        iterations=iterations,
        max_turns=max_turns,
        weaker_team_color=weaker_team_color,
        seed=seed
    )
    
    # Run the experiments
    experiment.run_experiments()
    
    return experiment


if __name__ == "__main__":
    # Run a test experiment with 1 iteration
    # RED team uses weaker model (claude-3-sonnet)
    # BLUE team uses stronger model (claude-3.7-sonnet)
    experiment = run_model_strength_experiment(
        weaker_model="anthropic/claude-3-sonnet",  # Weaker model
        stronger_model="anthropic/claude-3.7-sonnet",  # Stronger model
        judge_model="anthropic/claude-3.7-sonnet",  # Judge model (smartest)
        weaker_team_min=2,  # Start with 2 agents on the weaker team
        weaker_team_max=6,  # Test up to 3 agents on the weaker team
        weaker_team_step=1,  # Increase by 1
        stronger_team_size=2,  # Fixed 2 agents on the stronger team
        iterations=7,  # Just 1 iteration for testing
        weaker_team_color="RED"  # Assign the weaker model to RED team
    )
