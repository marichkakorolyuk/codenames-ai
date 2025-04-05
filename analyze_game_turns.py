#!/usr/bin/env python3
"""
Simple analysis of Codenames game results, focusing on average turns by win mechanism.
"""
import pandas as pd
import matplotlib.pyplot as plt

def analyze_turns_by_win_mechanism():
    """
    Analyze the average number of turns it takes to win/lose based on different win mechanisms:
    1. All cards revealed
    2. Assassin card revealed
    """
    print("Loading data from team_size_results.csv...")
    
    # Read the CSV file
    try:
        df = pd.read_csv('team_size_results.csv')
    except FileNotFoundError:
        print("Error: team_size_results.csv file not found. Please run the experiments first.")
        return
    
    # Get basic stats about the dataset
    total_games = len(df)
    print(f"Analyzing {total_games} games...")
    
    # Create a new column to categorize win mechanisms
    df['win_mechanism'] = df['win_reason'].apply(categorize_win_mechanism)
    
    # Calculate average turns by win mechanism
    win_mechanism_stats = df.groupby('win_mechanism')['turns_played'].agg(['mean', 'count']).reset_index()
    win_mechanism_stats = win_mechanism_stats.rename(columns={'mean': 'avg_turns', 'count': 'num_games'})
    win_mechanism_stats['percentage'] = (win_mechanism_stats['num_games'] / total_games * 100).round(1)
    
    # Sort by average turns
    win_mechanism_stats = win_mechanism_stats.sort_values('avg_turns')
    
    # Print results
    print("\nAverage Turns by Win Mechanism:")
    print("------------------------------")
    for _, row in win_mechanism_stats.iterrows():
        print(f"{row['win_mechanism']}: {row['avg_turns']:.2f} turns on average ({row['num_games']} games, {row['percentage']}%)")
    
    # Create a simple bar chart
    plt.figure(figsize=(10, 6))
    plt.bar(win_mechanism_stats['win_mechanism'], win_mechanism_stats['avg_turns'])
    plt.title('Average Number of Turns by Win Mechanism')
    plt.xlabel('Win Mechanism')
    plt.ylabel('Average Turns')
    plt.yticks(range(0, int(win_mechanism_stats['avg_turns'].max()) + 2))
    plt.tight_layout()
    plt.savefig('turns_by_win_mechanism.png')
    print("\nChart saved as 'turns_by_win_mechanism.png'")
    
    # Create a pie chart for win mechanism percentages
    plt.figure(figsize=(8, 8))
    plt.pie(win_mechanism_stats['num_games'], labels=win_mechanism_stats['win_mechanism'], 
            autopct='%1.1f%%', startangle=90, explode=[0.05] * len(win_mechanism_stats))
    plt.title('Percentage of Games by Win Mechanism')
    plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
    plt.savefig('win_mechanism_percentage.png')
    print("Chart saved as 'win_mechanism_percentage.png'")
    
    return win_mechanism_stats

def categorize_win_mechanism(reason):
    """Categorize win reasons into broader mechanisms."""
    if 'uncovering all their cards' in reason:
        return 'All cards revealed'
    elif 'ASSASSIN card' in reason:
        return 'Assassin card revealed'
    elif 'maximum turn limit' in reason:
        return 'Maximum turn limit reached'
    else:
        return 'Other'

if __name__ == "__main__":
    analyze_turns_by_win_mechanism()
