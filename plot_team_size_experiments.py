# plot_team_size_experiments.py
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
from datetime import datetime

def plot_win_rates_by_team_difference(csv_file):
    """
    Plot win rates by blue team size and team size difference from a CSV file
    
    Args:
        csv_file: Path to the CSV file containing experiment results
    """
    # Read the CSV file
    df = pd.read_csv(csv_file)
    
    # Group by blue team size AND team size difference and calculate win rates
    plot_data = df.groupby(['blue_team_size', 'team_size_difference']).agg({
        'red_win': 'mean', 
        'blue_win': 'mean',
        'red_team_size': 'mean',
        'turns_played': 'mean'
    }).reset_index()
    
    # Convert to percentages
    plot_data['red_win_rate'] = plot_data['red_win'] * 100
    plot_data['blue_win_rate'] = plot_data['blue_win'] * 100
    
    # Sort by blue team size and team size difference
    plot_data = plot_data.sort_values(['blue_team_size', 'team_size_difference'])
    
    # Create a figure
    plt.figure(figsize=(14, 8))
    
    # Get unique blue team sizes for different line styles
    blue_sizes = sorted(plot_data['blue_team_size'].unique())
    markers = ['o', 's', '^', 'D', 'v', '<', '>', 'p', '*']
    
    # Create a line for each blue team size
    for i, blue_size in enumerate(blue_sizes):
        subset = plot_data[plot_data['blue_team_size'] == blue_size]
        
        # Calculate the red team size based on blue size and difference
        subset = subset.copy()
        subset['red_team_size'] = subset['blue_team_size'] - subset['team_size_difference']
        
        marker = markers[i % len(markers)]
        
        # Plot RED team win rate
        plt.plot(subset['team_size_difference'], subset['red_win_rate'], 
                 marker=marker, linewidth=2, 
                 label=f'RED Win Rate (Blue Size={blue_size})', 
                 color='red', linestyle='-', alpha=0.7 + (i * 0.05))
        
        # Plot BLUE team win rate
        plt.plot(subset['team_size_difference'], subset['blue_win_rate'], 
                 marker=marker, linewidth=2, 
                 label=f'BLUE Win Rate (Blue Size={blue_size})', 
                 color='blue', linestyle='--', alpha=0.7 + (i * 0.05))
        
        # Add data annotations - simplified to avoid cluttering
        for _, row in subset.iterrows():
            # Only annotate if difference is a whole number to reduce clutter
            if row['team_size_difference'] == int(row['team_size_difference']):
                plt.annotate(f"R:{row['red_win_rate']:.0f}%", 
                           (row['team_size_difference'], row['red_win_rate']),
                           textcoords="offset points", 
                           xytext=(0,8), 
                           ha='center', fontsize=8)
                
                plt.annotate(f"B:{row['blue_win_rate']:.0f}%", 
                           (row['team_size_difference'], row['blue_win_rate']),
                           textcoords="offset points", 
                           xytext=(0,-12), 
                           ha='center', fontsize=8)
    
    # Add team size combinations to x-axis
    x_ticks = sorted(plot_data['team_size_difference'].unique())
    plt.xticks(x_ticks)
    
    # Add labels and title
    plt.xlabel('Team Size Difference (BLUE - RED)')
    plt.ylabel('Win Rate (%)')
    plt.title('Codenames Win Rates by Blue Team Size and Team Size Difference')
    
    # Add a legend with better positioning
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=3)
    
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
    plot_win_rates_by_team_difference(csv_file)