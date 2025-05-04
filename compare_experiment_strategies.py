#!/usr/bin/env python
# compare_experiment_strategies.py
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
import os

def compare_experiment_strategies(team_size_file, model_strength_file):
    """
    Compare the two different experiment strategies:
    - Team Size Experiment (using weak agent for turns resolution)
    - Model Strength Experiment (using strong agent for turns resolution)
    
    Args:
        team_size_file: Path to the team size experiment results CSV
        model_strength_file: Path to the model strength experiment results CSV
    """
    # Read both CSV files
    print(f"Reading data from {team_size_file}...")
    team_df = pd.read_csv(team_size_file)
    
    print(f"Reading data from {model_strength_file}...")
    model_df = pd.read_csv(model_strength_file)
    
    # Print basic information about the datasets
    print(f"\nTeam size dataset contains {len(team_df)} games")
    print(f"Model strength dataset contains {len(model_df)} games")
    
    # Calculate key statistics with confidence intervals
    
    # Function to calculate mean and 95% CI
    def calc_stats(data):
        mean = np.mean(data)
        ci = 1.96 * np.std(data) / np.sqrt(len(data))
        return mean, ci
    
    # Team Size Experiment (weak agent for turns resolution)
    team_turns_mean, team_turns_ci = calc_stats(team_df['turns_played'])
    
    # Model Strength Experiment (strong agent for turns resolution)
    model_turns_mean, model_turns_ci = calc_stats(model_df['turns_played'])
    
    # Prepare data for plotting
    categories = ['Weak Resolution Agent', 'Strong Resolution Agent']
    means = [team_turns_mean, model_turns_mean]
    errors = [team_turns_ci, model_turns_ci]
    
    # Print the statistics
    print("\n--- Comparison Statistics ---")
    print(f"Weak Agent (Team Size Experiment): {team_turns_mean:.2f} ± {team_turns_ci:.2f} turns")
    print(f"Strong Agent (Model Strength Experiment): {model_turns_mean:.2f} ± {model_turns_ci:.2f} turns")
    
    # Create the bar plot
    plt.figure(figsize=(10, 6))
    
    # Plot bars with error bars
    bars = plt.bar(categories, means, width=0.6, alpha=0.8, 
             color=['#3498db', '#e74c3c'])
    
    # Add error bars
    plt.errorbar(categories, means, yerr=errors, fmt='none', ecolor='black', 
                capsize=10, capthick=2, elinewidth=2)
    
    # Customize plot
    plt.title('Having Strong Agent for Disagreement Resolution Helps to Finish Game', fontsize=16)
    plt.ylabel('Average Number of Turns per Game', fontsize=12)
    plt.ylim(0, max(means) + max(errors) + 2)  # Add some headroom
    
    # Add value labels on top of bars
    for bar, mean, error in zip(bars, means, errors):
        plt.text(bar.get_x() + bar.get_width()/2, mean + error + 0.3,
                f'{mean:.2f} ± {error:.2f}', 
                ha='center', va='bottom', fontsize=12)
    
    # Add explanatory notes
    plt.figtext(0.5, 0.01, 
                "Strong resolution mechanics are important for resolving conflicts within teams\nWeak Agent = Team Size Experiment, Strong Agent = Model Strength Experiment", 
                ha="center", fontsize=10, style='italic')
    
    # Add grid lines for better readability
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Adjust layout
    plt.tight_layout(rect=[0, 0.05, 1, 0.95])
    
    # Generate timestamp for the output file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    plot_filename = f"strategy_comparison_{timestamp}.png"
    
    # Save the plot
    plt.savefig(plot_filename)
    print(f"Plot saved to {plot_filename}")
    
    # Show the plot
    plt.show()
    
    # Additional analysis - create a detailed comparison
    print("\n--- Detailed Comparison ---")
    
    # Win reasons
    team_all_cards = team_df[team_df['win_reason'].str.contains('uncovering all their cards')].shape[0]
    team_assassin_fails = team_df[team_df['win_reason'].str.contains('ASSASSIN')].shape[0]
    
    model_all_cards = model_df[model_df['win_reason'].str.contains('uncovering all their cards')].shape[0]
    model_assassin_fails = model_df[model_df['win_reason'].str.contains('ASSASSIN')].shape[0]
    
    print("Win Reasons:")
    print(f"  Weak Resolution Agent: {team_all_cards/len(team_df)*100:.1f}% all cards open, {team_assassin_fails/len(team_df)*100:.1f}% ASSASSIN reveals (communication failures)")
    print(f"  Strong Resolution Agent: {model_all_cards/len(model_df)*100:.1f}% all cards open, {model_assassin_fails/len(model_df)*100:.1f}% ASSASSIN reveals (communication failures)")
    
    # Create a second plot comparing win reasons
    plt.figure(figsize=(12, 7))
    
    # Data for stacked bar chart
    all_cards_percentages = [team_all_cards/len(team_df)*100, model_all_cards/len(model_df)*100]
    assassin_percentages = [team_assassin_fails/len(team_df)*100, model_assassin_fails/len(model_df)*100]
    
    # Create stacked bars
    plt.bar(categories, all_cards_percentages, label='All Cards Open', color='#2ecc71')
    plt.bar(categories, assassin_percentages, bottom=all_cards_percentages, 
            label='ASSASSIN Reveals (Communication Failure)', color='#e74c3c')
    
    # Add value labels on bars
    for i, (all_cards, assassin) in enumerate(zip(all_cards_percentages, assassin_percentages)):
        # Label for all cards open
        plt.text(i, all_cards/2, f'{all_cards:.1f}%', ha='center', va='center', 
                color='white', fontweight='bold', fontsize=12)
        
        # Label for assassin reveals
        plt.text(i, all_cards + assassin/2, f'{assassin:.1f}%', ha='center', va='center', 
                color='white', fontweight='bold', fontsize=12)
    
    # Customize plot
    plt.title('Strong Resolution Agents Help Teams Communicate Effectively', fontsize=16)
    plt.ylabel('Percentage of Games (%)', fontsize=12)
    plt.ylim(0, 105)  # Leave room for labels
    plt.legend(loc='upper right')
    
    # Add grid lines
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Adjust layout
    plt.tight_layout()
    
    # Save the win reasons plot
    win_reasons_filename = f"win_reasons_comparison_{timestamp}.png"
    plt.savefig(win_reasons_filename)
    print(f"Win reasons plot saved to {win_reasons_filename}")
    
    # Show the plot
    plt.show()

if __name__ == "__main__":
    # Default CSV files to read
    team_size_file = "team_size_results.csv"
    model_strength_file = "model_strength_results.csv"
    
    # Check if the default CSV files exist
    if not os.path.exists(team_size_file) or not os.path.exists(model_strength_file):
        print("Error: One or both CSV files not found.")
        if not os.path.exists(team_size_file):
            print(f"Missing: {team_size_file}")
        if not os.path.exists(model_strength_file):
            print(f"Missing: {model_strength_file}")
        exit(1)
    
    # Run the comparison
    compare_experiment_strategies(team_size_file, model_strength_file)
