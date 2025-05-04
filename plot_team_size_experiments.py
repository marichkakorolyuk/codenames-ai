# plot_team_size_experiments.py
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
from datetime import datetime

def plot_win_rates_by_team_difference(csv_file):
    """
    Plot win rates by team size difference from a CSV file with confidence intervals
    and simplified legend showing only 'Bigger Team' and 'Smaller Team'
    
    Args:
        csv_file: Path to the CSV file containing experiment results
    """
    # Read the CSV file
    df = pd.read_csv(csv_file)
    
    # For confidence intervals, we need to calculate win rates and std errors
    # First, create a column that identifies the bigger team based on team sizes
    df['bigger_team'] = df.apply(
        lambda row: 'BLUE' if row['blue_team_size'] > row['red_team_size'] else 'RED', 
        axis=1
    )
    
    # Group by team size difference and calculate statistics
    grouped = df.groupby('team_size_difference')
    
    # Initialize data structures for our plot
    diff_values = sorted(df['team_size_difference'].unique())
    bigger_team_win_rates = []
    bigger_team_std_errors = []
    smaller_team_win_rates = []
    smaller_team_std_errors = []
    
    # For each team size difference, calculate mean win rates and std errors
    for diff in diff_values:
        subset = df[df['team_size_difference'] == diff]
        
        # Calculate win rate for bigger team
        bigger_wins = subset.apply(
            lambda row: row['blue_win'] if row['blue_team_size'] > row['red_team_size'] else row['red_win'],
            axis=1
        )
        bigger_team_win_rate = bigger_wins.mean() * 100
        # Calculate standard error (95% confidence interval = 1.96 * std_error)
        bigger_team_std_err = 1.96 * (bigger_wins.std() / np.sqrt(len(subset))) * 100
        
        # Calculate win rate for smaller team
        smaller_wins = subset.apply(
            lambda row: row['blue_win'] if row['blue_team_size'] <= row['red_team_size'] else row['red_win'],
            axis=1
        )
        smaller_team_win_rate = smaller_wins.mean() * 100
        # Calculate standard error (95% confidence interval = 1.96 * std_error)
        smaller_team_std_err = 1.96 * (smaller_wins.std() / np.sqrt(len(subset))) * 100
        
        # Store results
        bigger_team_win_rates.append(bigger_team_win_rate)
        bigger_team_std_errors.append(bigger_team_std_err)
        smaller_team_win_rates.append(smaller_team_win_rate)
        smaller_team_std_errors.append(smaller_team_std_err)
    
    # Create a figure
    plt.figure(figsize=(14, 8))
    
    # Plot shaded confidence interval for bigger team
    plt.fill_between(
        diff_values, 
        [rate - err for rate, err in zip(bigger_team_win_rates, bigger_team_std_errors)],
        [rate + err for rate, err in zip(bigger_team_win_rates, bigger_team_std_errors)],
        alpha=0.15, color='blue'
    )
    
    # Plot line and markers for bigger team
    plt.plot(
        diff_values, bigger_team_win_rates,
        marker='o', linewidth=2,
        label='Bigger Team', color='blue', linestyle='-'
    )
    
    # Plot shaded confidence interval for smaller team
    plt.fill_between(
        diff_values, 
        [rate - err for rate, err in zip(smaller_team_win_rates, smaller_team_std_errors)],
        [rate + err for rate, err in zip(smaller_team_win_rates, smaller_team_std_errors)],
        alpha=0.15, color='red'
    )
    
    # Plot line and markers for smaller team
    plt.plot(
        diff_values, smaller_team_win_rates,
        marker='s', linewidth=2,
        label='Smaller Team', color='red', linestyle='--'
    )
    
    # Add data annotations for clarity
    for i, diff in enumerate(diff_values):
        # Annotate bigger team win rate
        plt.annotate(
            f"{bigger_team_win_rates[i]:.0f}%",
            (diff, bigger_team_win_rates[i]),
            textcoords="offset points",
            xytext=(0, 10),
            ha='center', fontsize=9
        )
        
        # Annotate smaller team win rate
        plt.annotate(
            f"{smaller_team_win_rates[i]:.0f}%",
            (diff, smaller_team_win_rates[i]),
            textcoords="offset points",
            xytext=(0, -15),
            ha='center', fontsize=9
        )
    
    # Add team size combinations to x-axis
    plt.xticks(diff_values)
    
    # Add labels and title
    plt.xlabel('Team Size Difference (BLUE - RED)')
    plt.ylabel('Win Rate (%)')
    plt.title('Just Having a Bigger Team Doesn\'t Help to Win Codenames\n(Win Rates by Team Size with 95% Confidence Intervals)')
    
    # Add a cleaner legend with only 2 entries
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.12), ncol=2, fontsize=12)
    
    # Add grid lines
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Add a reference line at 50%
    plt.axhline(y=50, color='gray', linestyle='--', alpha=0.5)
    
    # Set y-axis limits
    plt.ylim(0, 105)
    
    # Adjust layout
    plt.tight_layout()
    
    # Generate timestamp for the output file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    plot_filename = f"team_size_plot_{timestamp}.png"
    
    # Save the plot
    plt.savefig(plot_filename)
    print(f"Plot saved to {plot_filename}")
    
    # Display the plot
    plt.show()

if __name__ == "__main__":
    # Default CSV file to read
    default_csv = "team_size_results.csv"
    
    # Check if the default CSV exists, otherwise let user specify
    if not os.path.exists(default_csv):
        csv_file = input(f"CSV file '{default_csv}' not found. Enter path to results CSV: ")
    else:
        # analyse_victory_reason_and_turns.py
        import pandas as pd
        import matplotlib.pyplot as plt
        import seaborn as sns
        import numpy as np
        import os
        from datetime import datetime
        
        def analyze_victory_reasons_and_turns(csv_file):
            """
            Analyze the relationship between victory reasons and number of turns played
            
            Args:
                csv_file: Path to the CSV file containing experiment results
            """
            # Read the CSV file
            print(f"Reading data from {csv_file}...")
            df = pd.read_csv(csv_file)
            
            # Print basic information about the dataset
            print(f"\nDataset contains {len(df)} games")
            print(f"Columns: {', '.join(df.columns)}")
            
            # 1. Create a summary of turns played by win_reason
            turnscsv_file = default_csv
        
    # Plot the win rates
    plot_win_rates_by_team_difference('team_size_results.csv')