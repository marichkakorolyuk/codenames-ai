#!/usr/bin/env python3
# plot_model_strength_experiments.py
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os
from datetime import datetime

def plot_win_rates_by_team_size(csv_file):
    """
    Plot win rates for weaker vs stronger model based on team size combinations
    
    Args:
        csv_file: Path to the CSV file containing model strength experiment results
    """
    # Read the CSV file
    try:
        df = pd.read_csv(csv_file, on_bad_lines='warn')
        print(f"Successfully loaded {len(df)} records from {csv_file}")
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return
    
    # Display basic information about the dataset
    print(f"\nColumns in dataset: {', '.join(df.columns)}")
    print(f"Unique weaker models: {df['weaker_model'].unique()}")
    print(f"Unique stronger models: {df['stronger_model'].unique()}")
    print(f"Weaker team sizes: {sorted(df['weaker_team_size'].unique())}")
    print(f"Stronger team sizes: {sorted(df['stronger_team_size'].unique())}")
    
    # Group by team sizes and calculate win rates
    plot_data = df.groupby(['weaker_team_size', 'stronger_team_size']).agg({
        'weaker_team_won': ['mean', 'sum', 'count'],
        'stronger_team_won': ['mean', 'sum'],
        'turns_played': 'mean',
        'game_duration': 'mean'
    }).reset_index()
    
    # Flatten the multi-level columns
    plot_data.columns = ['_'.join(col).strip('_') for col in plot_data.columns.values]
    
    # Convert to percentages
    plot_data['weaker_team_won_mean'] *= 100
    plot_data['stronger_team_won_mean'] *= 100
    
    # Calculate confidence intervals (95%)
    z = 1.96  # 95% confidence level
    
    # Calculate confidence interval just for weaker team (which has count data)
    n = plot_data['weaker_team_won_count']
    p = plot_data['weaker_team_won_mean'] / 100
    
    # Calculate standard error and confidence interval
    plot_data['weaker_team_ci'] = z * np.sqrt((p * (1 - p)) / n) * 100
    
    # For stronger team, use the same count since they're from the same games
    p_stronger = plot_data['stronger_team_won_mean'] / 100
    plot_data['stronger_team_ci'] = z * np.sqrt((p_stronger * (1 - p_stronger)) / n) * 100
    
    # Create the main figure for win rates by team size
    plt.figure(figsize=(14, 10))
    
    # Calculate team size ratio for x-axis
    plot_data['team_size_ratio'] = plot_data['weaker_team_size'] / plot_data['stronger_team_size']
    
    # Sort by team size ratio
    plot_data = plot_data.sort_values('team_size_ratio')
    
    # Create bar width and positions
    bar_width = 0.35
    x = np.arange(len(plot_data))
    
    # Create grouped bar chart
    ax1 = plt.subplot(2, 1, 1)
    
    # Plot weaker team win rate
    weaker_bars = ax1.bar(x - bar_width/2, plot_data['weaker_team_won_mean'], 
                          bar_width, color='green', alpha=0.7, 
                          label='Weaker Model Win Rate')
    
    # Plot stronger team win rate
    stronger_bars = ax1.bar(x + bar_width/2, plot_data['stronger_team_won_mean'], 
                           bar_width, color='purple', alpha=0.7,
                           label='Stronger Model Win Rate')
    
    # Add error bars
    ax1.errorbar(x - bar_width/2, plot_data['weaker_team_won_mean'], 
                yerr=plot_data['weaker_team_ci'], fmt='none', capsize=5, 
                color='black', alpha=0.7)
    
    ax1.errorbar(x + bar_width/2, plot_data['stronger_team_won_mean'], 
                yerr=plot_data['stronger_team_ci'], fmt='none', capsize=5, 
                color='black', alpha=0.7)
    
    # Add data labels to bars
    def add_labels(bars):
        for bar in bars:
            height = bar.get_height()
            ax1.annotate(f'{height:.1f}%',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),  # 3 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=9)
    
    add_labels(weaker_bars)
    add_labels(stronger_bars)
    
    # Set x-ticks with team size combinations
    plt.xticks(x, [f"W:{row['weaker_team_size']}, S:{row['stronger_team_size']} (Ratio: {row['team_size_ratio']:.1f})" 
                  for _, row in plot_data.iterrows()], rotation=45, ha='right')
    
    # Add a reference line at 50%
    plt.axhline(y=50, color='gray', linestyle='--', alpha=0.5)
    
    # Add labels and title
    plt.ylabel('Win Rate (%)')
    plt.title('Win Rates by Team Size Combination (Weaker vs Stronger Model)')
    plt.legend(loc='upper right')
    plt.ylim(0, 105)  # Ensure y axis goes from 0 to 100%
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Add second plot for game statistics
    ax2 = plt.subplot(2, 1, 2)
    
    # Plot average turns played
    turns_line = ax2.plot(x, plot_data['turns_played_mean'], 'o-', 
                         color='blue', label='Avg. Turns Played')
    
    # Set up primary y-axis for turns
    ax2.set_ylabel('Average Turns Played', color='blue')
    ax2.tick_params(axis='y', labelcolor='blue')
    ax2.set_ylim(bottom=0)
    
    # Set up secondary y-axis for game duration
    ax3 = ax2.twinx()
    duration_line = ax3.plot(x, plot_data['game_duration_mean'] / 60, 'o-', 
                            color='red', label='Avg. Game Duration (min)')
    
    ax3.set_ylabel('Average Game Duration (minutes)', color='red')
    ax3.tick_params(axis='y', labelcolor='red')
    ax3.set_ylim(bottom=0)
    
    # Set x-ticks with team size combinations
    ax2.set_xticks(x)
    ax2.set_xticklabels([f"W:{row['weaker_team_size']}, S:{row['stronger_team_size']} (Ratio: {row['team_size_ratio']:.1f})" 
                  for _, row in plot_data.iterrows()], rotation=45, ha='right')
    
    # Add title
    ax2.set_title('Game Duration and Turns by Team Size Combination')
    
    # Add combined legend
    lines1, labels1 = ax2.get_legend_handles_labels()
    lines2, labels2 = ax3.get_legend_handles_labels()
    ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
    
    # Grid for second plot
    ax2.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Adjust layout
    plt.tight_layout()
    
    # Generate timestamp for the output file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    plot_filename = f"model_strength_plot_{timestamp}.png"
    
    # Save the plot
    plt.savefig(plot_filename)
    print(f"Plot saved to {plot_filename}")
    
    # Generate detailed statistics
    print("\n=== Detailed Win Rate Statistics ===")
    stats_table = plot_data[['weaker_team_size', 'stronger_team_size', 'team_size_ratio',
                            'weaker_team_won_mean', 'stronger_team_won_mean', 
                            'weaker_team_won_sum', 'stronger_team_won_sum',
                            'weaker_team_won_count']]
    
    # Rename columns for clarity
    stats_table = stats_table.rename(columns={
        'weaker_team_won_mean': 'Weaker Win %',
        'stronger_team_won_mean': 'Stronger Win %',
        'weaker_team_won_sum': 'Weaker Wins',
        'stronger_team_won_sum': 'Stronger Wins',
        'weaker_team_won_count': 'Games Played'
    })
    
    print(stats_table.to_string(index=False, float_format='%.2f'))
    
    # Show the plot
    plt.show()

def analyze_win_reasons(csv_file):
    """
    Analyze the reasons behind wins for both weaker and stronger models
    
    Args:
        csv_file: Path to the CSV file containing model strength experiment results
    """
    # Read the CSV file
    df = pd.read_csv(csv_file, on_bad_lines='warn')
    
    # Create a figure
    plt.figure(figsize=(12, 7))
    
    # Group data by win reason and which model won
    win_reasons = df.groupby(['win_reason', 'weaker_team_won']).size().reset_index(name='count')
    
    # Define which team won
    win_reasons['Winner'] = win_reasons['weaker_team_won'].apply(lambda x: 'Weaker Model' if x == 1 else 'Stronger Model')
    
    # Create the grouped bar chart
    sns.barplot(data=win_reasons, x='win_reason', y='count', hue='Winner', palette=['green', 'purple'])
    
    # Add title and labels
    plt.title('Win Reasons by Model Strength')
    plt.xlabel('Win Reason')
    plt.ylabel('Count')
    plt.xticks(rotation=45, ha='right')
    
    # Adjust layout
    plt.tight_layout()
    
    # Generate timestamp for the output file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    plot_filename = f"win_reasons_plot_{timestamp}.png"
    
    # Save the plot
    plt.savefig(plot_filename)
    print(f"Win reasons plot saved to {plot_filename}")
    
def analyze_model_strength_results(csv_file):
    """
    Main function to analyze model strength results
    
    Args:
        csv_file: Path to the CSV file containing experiment results
    """
    print(f"\n=== Analyzing Model Strength Experiment Results ===")
    print(f"Reading data from: {csv_file}")
    
    # Plot win rates by team size
    plot_win_rates_by_team_size(csv_file)
    
    # Analyze win reasons
    analyze_win_reasons(csv_file)
    
    print("\n=== Analysis Complete ===")

if __name__ == "__main__":
    # Default CSV file to read
    default_csv = "model_strength_results.csv"
    
    # Check if the default CSV exists, otherwise let user specify
    if not os.path.exists(default_csv):
        csv_file = input(f"CSV file '{default_csv}' not found. Enter path to results CSV: ")
    else:
        csv_file = default_csv
    
    # Analyze the model strength experiment results
    analyze_model_strength_results(csv_file)
