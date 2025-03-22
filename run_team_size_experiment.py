import os
import time
import sys
import weave

from experiment_team_size import run_experiment

def main():
    """
    Run a Codenames experiment with fixed red team size (2) and varying blue team sizes.
    
    Configuration:
    - Red team size: Fixed at 2 operatives
    - Blue team sizes: 2, 4, 6, and 8 operatives
    - Iterations: 5 games per configuration
    """
    print("Starting Codenames Team Size Experiment...")
    print("- Red team size: Fixed at 2 operatives")
    print("- Blue team sizes: [2, 4, 6, 8] operatives") 
    print("- Iterations: 5 games per configuration")
    print("- Total games to run: 20")
    print("\nExperiment progress will be displayed below. This may take some time...")
    
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    
    # Run the experiment with the specified parameters
    experiment = run_experiment(
        # Fix red team size at 2
        red_team_min=2,
        red_team_max=2, 
        red_team_step=1,
        
        # Vary blue team size from 2 to 8
        blue_team_min=2,
        blue_team_max=4,
        blue_team_step=2,
        
        # Run 5 iterations per configuration
        iterations=1,
        
        # Maximum turns per game
        max_turns=2,
        
        # Generate plots automatically
        plot_results=True
    )
    
    # Results are automatically saved during the experiment run
    
    print("\nExperiment completed!")
    print(f"Results saved to CSV and plot generated.")
    
    # Return the experiment object for potential additional analysis
    return experiment

if __name__ == "__main__":
    main()

