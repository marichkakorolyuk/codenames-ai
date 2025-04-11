import os
import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import List, Dict, Any, Tuple
import random


# Import the game function
from updated_play_codenames_game_standalone import play_codenames_game, CardType

class ExperimentRunner:
    """Class to run Codenames experiments with varying team sizes"""

    def __init__(self, 
                 red_team_min, 
                 red_team_max, 
                 red_team_step,
                 blue_team_min, 
                 blue_team_max, 
                 blue_team_step,
                 iterations,
                 max_turns,
                 use_wandb: bool = True,
                 use_plots: bool = False,
                 seed: int = None):
        """
        Initialize the experiment runner
        
        Args:
            red_team_min: Minimum size for the RED team
            red_team_max: Maximum size for the RED team
            red_team_step: Step size for increasing RED team
            blue_team_min: Minimum size for the BLUE team
            blue_team_max: Maximum size for the BLUE team
            blue_team_step: Step size for increasing BLUE team 
            iterations: Number of games to run per configuration
            max_turns: Maximum number of turns per game
            seed: Random seed for reproducibility (None for random)
        """
        self.red_team_min = red_team_min
        self.red_team_max = red_team_max
        self.red_team_step = red_team_step
        self.blue_team_min = blue_team_min
        self.blue_team_max = blue_team_max
        self.blue_team_step = blue_team_step
        self.iterations = iterations
        self.max_turns = max_turns
        self.seed = seed
        self.results_df = None

        self.use_wandb = use_wandb
        self.use_plots = use_plots
        
        if use_wandb:
            import wandb
            wandb.init(project="codenames-ai")
        
    def _get_red_team_sizes(self) -> List[int]:
        """Generate a list of RED team sizes based on min, max, and step"""
        return list(range(self.red_team_min, self.red_team_max + 1, self.red_team_step))
        
    def _get_blue_team_sizes(self) -> List[int]:
        """Generate a list of BLUE team sizes based on min, max, and step"""
        return list(range(self.blue_team_min, self.blue_team_max + 1, self.blue_team_step))
        
    def run_experiments(self) -> pd.DataFrame:
        """
        Run experiments with various team sizes and record the results
        
        Returns:
            DataFrame containing the experiment results
        """
        # Initialize empty list to store experiment results
        results = []
        
        # Create timestamp for this experiment run
        self.timestamp = time.strftime("%Y%m%d-%H%M%S")
        
        # Get the list of team sizes to test
        red_team_sizes = self._get_red_team_sizes()
        blue_team_sizes = self._get_blue_team_sizes()
        
        # Calculate total number of games to run
        total_games = len(red_team_sizes) * len(blue_team_sizes) * self.iterations
        games_completed = 0
        
        print(f"\n=== Starting Codenames Team Size Experiments ===")
        print(f"RED team sizes: {red_team_sizes}")
        print(f"BLUE team sizes: {blue_team_sizes}")
        print(f"Iterations per configuration: {self.iterations}")
        print(f"Total games to run: {total_games}")
        print(f"Results will be automatically saved to: codenames_experiment_results_{self.timestamp}.csv")
        
        # Record start time for the entire experiment
        experiment_start_time = time.time()
        
        # Create the base filename for saved results
        self.base_filename = f"codenames_experiment_results_{self.timestamp}"
        self.snapshot_count = 0
        
        try:
            # Run experiments for each team size combination
            for red_team_size in red_team_sizes:
                for blue_team_size in blue_team_sizes:
                    print(f"\nTesting with RED team size = {red_team_size}, BLUE team size = {blue_team_size}")
                    
                    # Run multiple iterations for each configuration
                    for iteration in range(1, self.iterations + 1):
                        try:
                            # Create a unique seed for this game if a base seed is provided
                            game_seed = None
                            if self.seed is not None:
                                game_seed = self.seed + (red_team_size * 10000) + (blue_team_size * 1000) + iteration
                            
                            print(f"  Running iteration {iteration}/{self.iterations}...")
                            
                            # Start time for this specific game
                            game_start_time = time.time()
                            
                            # Run the game
                            game_state, game_outcome = play_codenames_game(
                                team_red_size=red_team_size,
                                team_blue_size=blue_team_size,
                                max_turns=self.max_turns,
                                seed=game_seed
                            )
                            
                            # Calculate game duration
                            game_duration = time.time() - game_start_time
                            
                            # Record the results
                            result = {
                                'red_team_size': red_team_size,
                                'blue_team_size': blue_team_size,
                                'team_size_difference': blue_team_size - red_team_size,
                                'iteration': iteration,
                                'winner': game_outcome['winner'],
                                'red_win': 1 if game_outcome['winner'] == 'RED' else 0,
                                'blue_win': 1 if game_outcome['winner'] == 'BLUE' else 0,
                                'turns_played': game_outcome['turns_played'],
                                'win_reason': game_outcome['win_reason'],
                                'game_duration': game_outcome['game_duration_seconds'],

                            }


                            if self.use_wandb:
                                import wandb
                                print("Logging to Weights & Biases...")
                                wandb.log(result)
                            
                            results.append(result)
                            
                            # Create a temporary dataframe with accumulated results so far
                            temp_df = pd.DataFrame(results)
                            
                            # Save results after each game as a safeguard - overwrite the main file
                            temp_df.to_csv(f"{self.base_filename}.csv", index=False)
                            
                            # Update progress
                            games_completed += 1
                            print(f"  Game completed: {games_completed}/{total_games} ({(games_completed/total_games)*100:.1f}%)")
                            
                            # Save a snapshot every 10 games
                            if games_completed % 10 == 0:
                                self._save_snapshot(temp_df)
                                
                        except Exception as e:

                            print(f"Error during game execution: {e}")
                            # print traceback
                            import traceback
                            traceback.print_exc()
                            
                            # Save what we have so far, even on error
                            if results:
                                temp_df = pd.DataFrame(results)
                                temp_df.to_csv(f"{self.base_filename}_error_{games_completed}.csv", index=False)
        
        except Exception as e:
            print(f"Exception during experiment: {e}")
            # Make sure to save results even on error
            if results:
                temp_df = pd.DataFrame(results)
                temp_df.to_csv(f"{self.base_filename}_error.csv", index=False)
        
        finally:
            # Always create the final dataframe and save it
            if results:
                self.results_df = pd.DataFrame(results)
                # Save one final time
                self.results_df.to_csv(f"{self.base_filename}_final.csv", index=False)
                
    def _save_snapshot(self, df):
        """Save a snapshot of current results to avoid data loss"""
        self.snapshot_count += 1
        snapshot_filename = f"{self.base_filename}_snapshot_{self.snapshot_count}.csv"
        df.to_csv(snapshot_filename, index=False)
        print(f"  Saved snapshot to {snapshot_filename} after {len(df)} games")
        
        # Create DataFrame from results
        self.results_df = df
        
        # Calculate experiment duration
        experiment_duration = time.time() - experiment_start_time
        print(f"\nExperiment completed in {experiment_duration:.2f} seconds")
        
        # Display summary statistics
        self._display_summary()
        
        return self.results_df
    
    def _display_summary(self):
        """Display summary statistics from the experiments"""
        if self.results_df is None:
            print("No results available. Run experiments first.")
            return
        
        print("\n=== Experiment Summary ===")
        
        # Group by team sizes and calculate win rates
        summary = self.results_df.groupby(['red_team_size', 'blue_team_size']).agg({
            'red_win': 'mean',
            'blue_win': 'mean',
            'turns_played': 'mean',
            'game_duration': 'mean',
            'total_tokens': 'mean',
        }).reset_index()
        
        # Rename columns for clarity
        summary = summary.rename(columns={
            'red_win': 'red_win_rate',
            'blue_win': 'blue_win_rate',
            'turns_played': 'avg_turns',
            'game_duration': 'avg_duration',
            'total_tokens': 'avg_tokens'
        })
        
        # Convert win rates to percentages
        summary['red_win_rate'] = summary['red_win_rate'] * 100
        summary['blue_win_rate'] = summary['blue_win_rate'] * 100
        
        # Display the summary
        print(summary.to_string(index=False, float_format=lambda x: f"{x:.2f}"))
    
    def save_results(self, filename: str = None):
        """Save the experiment results to a CSV file"""
        if self.results_df is None:
            print("No results available. Run experiments first.")
            return
        
        # If no filename is provided, use the base filename with timestamp
        if filename is None:
            if hasattr(self, 'base_filename'):
                filename = f"{self.base_filename}.csv"
            else:
                # Create a timestamp if we don't have one yet
                timestamp = time.strftime("%Y%m%d-%H%M%S")
                filename = f"codenames_experiment_results_{timestamp}.csv"
        
        self.results_df.to_csv(filename, index=False)
        print(f"Results saved to {filename}")
        
        # Also save a copy with team size info in the filename for easier identification
        red_sizes = self._get_red_team_sizes()
        blue_sizes = self._get_blue_team_sizes()
        size_info = f"R{min(red_sizes)}-{max(red_sizes)}_B{min(blue_sizes)}-{max(blue_sizes)}"
        size_filename = filename.replace('.csv', f'_{size_info}.csv')
        self.results_df.to_csv(size_filename, index=False)
        print(f"Size-labeled copy saved to {size_filename}")
    
    def plot_win_rates(self, save_path: str = None):
        """
        Plot win rates by team size difference
        
        Args:
            save_path: Path to save the plot image (None to display only)
        """
        if self.results_df is None:
            print("No results available. Run experiments first.")
            return
            
        # Create multiple plots for better analysis
        if self.use_plots:
            self._plot_by_team_difference(save_path)
            self._plot_by_team_sizes(save_path)
            
    def _plot_by_team_difference(self, save_path: str = None):
        """Plot win rates by team size difference"""
        # Group by team size difference and calculate win rates
        plot_data = self.results_df.groupby('team_size_difference').agg({
            'red_win': 'mean',
            'blue_win': 'mean',
            'red_team_size': 'mean',  # Average red team size for each difference group
            'blue_team_size': 'mean'  # Average blue team size for each difference group
        }).reset_index()
        
        # Convert win rates to percentages
        plot_data['red_win_rate'] = plot_data['red_win'] * 100
        plot_data['blue_win_rate'] = plot_data['blue_win'] * 100
        
        # Sort by team size difference
        plot_data = plot_data.sort_values('team_size_difference')
        
        # Create a figure
        plt.figure(figsize=(12, 7))
        
        # Create a bar chart
        bar_width = 0.35
        x = np.arange(len(plot_data))
        
        # Plot RED team win rate
        plt.bar(x - bar_width/2, plot_data['red_win_rate'], 
                bar_width, label='RED Win Rate', color='red', alpha=0.7)
        
        # Plot BLUE team win rate
        plt.bar(x + bar_width/2, plot_data['blue_win_rate'], 
                bar_width, label='BLUE Win Rate', color='blue', alpha=0.7)
        
        # Add labels and title
        plt.xlabel('Team Size Difference (BLUE - RED)')
        plt.ylabel('Win Rate (%)')
        plt.title('Codenames Win Rates by Team Size Difference')
        
        # Set x-tick labels to show the difference with average team sizes
        plt.xticks(x, [f"{diff} (R≈{red:.1f}, B≈{blue:.1f})" for diff, red, blue in 
                      zip(plot_data['team_size_difference'], 
                          plot_data['red_team_size'],
                          plot_data['blue_team_size'])])
        
        # Add a legend
        plt.legend()
        
        # Add grid lines
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        
        # Add a reference line at 50%
        plt.axhline(y=50, color='gray', linestyle='--', alpha=0.5)
        
        # Adjust layout
        plt.tight_layout()
        
        # Save the plot if a path is provided
        if save_path:
            diff_plot_path = save_path.replace('.png', '_by_difference.png')
            plt.savefig(diff_plot_path)
            print(f"Team difference plot saved to {diff_plot_path}")
            
        plt.show()
        
    def _plot_by_team_sizes(self, save_path: str = None):
        """Plot win rates by actual team sizes as a heatmap"""
        # Group by both team sizes and calculate win rates
        heatmap_data = self.results_df.groupby(['red_team_size', 'blue_team_size']).agg({
            'red_win': 'mean',
            'blue_win': 'mean',
            'turns_played': 'mean'
        }).reset_index()
        
        # Convert the data to a pivot table for the heatmap (red win rate)
        red_pivot = heatmap_data.pivot(index='red_team_size', 
                                        columns='blue_team_size', 
                                        values='red_win')
        
        # Create a figure with two subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))
        
        # First heatmap - RED team win rate
        sns = plt
        cmap = 'Reds'
        heatmap1 = sns.heatmap(red_pivot * 100, annot=True, fmt='.1f', cmap=cmap, ax=ax1,
                    vmin=0, vmax=100, cbar_kws={'label': 'Win Rate (%)'})
        ax1.set_title('RED Team Win Rate by Team Sizes')
        ax1.set_xlabel('BLUE Team Size')
        ax1.set_ylabel('RED Team Size')
        
        # Second heatmap - Average turns played
        turns_pivot = heatmap_data.pivot(index='red_team_size', 
                                        columns='blue_team_size', 
                                        values='turns_played')
        cmap2 = 'viridis'
        heatmap2 = sns.heatmap(turns_pivot, annot=True, fmt='.1f', cmap=cmap2, ax=ax2,
                    cbar_kws={'label': 'Average Turns Played'})
        ax2.set_title('Average Game Length by Team Sizes')
        ax2.set_xlabel('BLUE Team Size')
        ax2.set_ylabel('RED Team Size')
        
        # Adjust layout
        plt.tight_layout()
        
        # Save the plot if a path is provided
        if save_path:
            sizes_plot_path = save_path.replace('.png', '_by_team_sizes.png')
            plt.savefig(sizes_plot_path)
            print(f"Team sizes plot saved to {sizes_plot_path}")
            
        plt.show()



def run_experiment(red_team_min: int = 2, 
                   red_team_max: int = 8, 
                   red_team_step: int = 2,
                   blue_team_min: int = 2, 
                   blue_team_max: int = 8, 
                   blue_team_step: int = 2,
                   iterations: int = 3,
                   max_turns: int = 20,
                   seed: int = None,
                   plot_results: bool = False):
    """
    Run a full experiment with the specified parameters
    
    Args:
        red_team_min: Minimum size for the RED team
        red_team_max: Maximum size for the RED team
        red_team_step: Step size for increasing RED team
        blue_team_min: Minimum size for the BLUE team
        blue_team_max: Maximum size for the BLUE team
        blue_team_step: Step size for increasing BLUE team 
        iterations: Number of games to run per configuration
        max_turns: Maximum number of turns per game
        seed: Random seed for reproducibility (None for random)
        plot_results: Whether to generate and display plots
    
    Returns:
        The experiment runner object containing the results
    """

    # Create and run the experiment
    experiment = ExperimentRunner(
        red_team_min=red_team_min,
        red_team_max=red_team_max,
        red_team_step=red_team_step,
        blue_team_min=blue_team_min,
        blue_team_max=blue_team_max,
        blue_team_step=blue_team_step,
        iterations=iterations,
        max_turns=max_turns,
        seed=seed
    )
    
    # Run the experiments
    experiment.run_experiments()
    
    # Now results are always saved in run_experiments method
    # Plot results if requested
    if plot_results:
        # Create timestamp-based plot path
        if hasattr(experiment, 'timestamp'):
            timestamp = experiment.timestamp
        else:
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            
        plot_path = f"codenames_experiment_plot_{timestamp}.png"
        experiment.plot_win_rates(plot_path)
    
    return experiment

if __name__ == "__main__":
    # Run an experiment with both RED and BLUE teams varying from 2 to 8 in steps of 2
    # Each configuration runs 3 times
  
    experiment = run_experiment(
        red_team_min=2,
        red_team_max=2,
        red_team_step=2,
        blue_team_min=2,
        blue_team_max=4,
        blue_team_step=2,
        iterations=1
    )
