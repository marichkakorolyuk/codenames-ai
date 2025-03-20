import pandas as pd
import matplotlib.pyplot as plt
import glob
import os
import numpy as np
import scipy.stats as stats

# Function to calculate confidence interval using bootstrap
def bootstrap_ci(data, n_bootstrap=1000, confidence=0.95):
    if len(data) <= 1:
        return 0, 0  # Not enough data for bootstrap
    
    # Convert to numpy array if it's not already
    data_array = np.array(data)
    
    # Bootstrap resampling
    bootstrap_samples = np.random.choice(data_array, size=(n_bootstrap, len(data_array)), replace=True)
    bootstrap_means = np.mean(bootstrap_samples, axis=1)
    
    # Calculate confidence intervals
    lower_bound = np.percentile(bootstrap_means, (1 - confidence) * 100 / 2)
    upper_bound = np.percentile(bootstrap_means, 100 - (1 - confidence) * 100 / 2)
    
    return lower_bound, upper_bound

# Find all experiment result CSV files
csv_files = glob.glob('codenames_experiment_results_*.csv')
print(f"Found {len(csv_files)} CSV files: {csv_files}")

# Read and merge all CSV files
all_data = []
for file in csv_files:
    df = pd.read_csv(file)
    all_data.append(df)
    print(f"Loaded {file} with {len(df)} rows")

# Combine all dataframes
merged_df = pd.concat(all_data, ignore_index=True)
print(f"Total merged dataset size: {len(merged_df)} rows")

# Save the merged data for reference
merged_output_file = 'merged_experiment_results.csv'
merged_df.to_csv(merged_output_file, index=False)
print(f"Merged data saved to {merged_output_file}")

# Calculate the team size difference (blue - red) as requested
merged_df['team_size_difference'] = merged_df['blue_team_size'] - merged_df['red_team_size']

# Group by red team size and team size difference
# Group raw data for bootstrap CI calculation
results = []
for (red_size, diff), group in merged_df.groupby(['red_team_size', 'team_size_difference']):
    total_games = len(group)
    blue_wins = sum(group['blue_win'])
    blue_win_percentage = (blue_wins / total_games) * 100
    
    # Calculate confidence intervals using bootstrap if possible
    if total_games > 1:
        # Create array of 0s and 1s for bootstrap
        blue_win_array = group['blue_win'].values
        lower_ci, upper_ci = bootstrap_ci(blue_win_array)
        lower_ci *= 100  # Convert to percentage
        upper_ci *= 100  # Convert to percentage
    else:
        # Not enough data for bootstrap, use binomial confidence interval
        if blue_wins == 0 or blue_wins == total_games:
            # Edge case handling for 0% or 100% win rates
            # Using adjusted Wald method for small samples
            z = stats.norm.ppf(0.975)  # 95% confidence
            adjust = 1/(2*total_games)
            p_adj = (blue_wins + adjust) / (total_games + 2*adjust)
            ci_width = z * np.sqrt((p_adj * (1 - p_adj)) / (total_games + 2*adjust))
            lower_ci = max(0, (p_adj - ci_width) * 100)
            upper_ci = min(100, (p_adj + ci_width) * 100)
        else:
            # Normal approximation to binomial
            z = stats.norm.ppf(0.975)
            p = blue_wins / total_games
            ci_width = z * np.sqrt((p * (1 - p)) / total_games)
            lower_ci = max(0, (p - ci_width) * 100)
            upper_ci = min(100, (p + ci_width) * 100)
    
    results.append({
        'red_team_size': red_size,
        'team_size_difference': diff,
        'total_games': total_games,
        'blue_wins': blue_wins,
        'blue_win_percentage': blue_win_percentage,
        'lower_ci': lower_ci,
        'upper_ci': upper_ci
    })

results_df = pd.DataFrame(results)
print("\nResults summary with confidence intervals:")
print(results_df[['red_team_size', 'team_size_difference', 'blue_win_percentage', 'lower_ci', 'upper_ci']])

# Get unique red team sizes
red_team_sizes = sorted(results_df['red_team_size'].unique())

# Create a more professional looking plot
plt.figure(figsize=(10, 6))

# Color palette
colors = plt.cm.viridis(np.linspace(0, 0.8, len(red_team_sizes)))

# Plot a line for each red team size
for i, red_size in enumerate(red_team_sizes):
    data = results_df[results_df['red_team_size'] == red_size]
    
    # Sort by team size difference for proper line plotting
    data = data.sort_values('team_size_difference')
    
    # Plot the main line
    plt.plot(data['team_size_difference'], data['blue_win_percentage'], 
             marker='o', label=f'Red Team Size = {red_size}',
             linewidth=2, color=colors[i], markersize=8)
    
    # Add confidence interval
    plt.fill_between(data['team_size_difference'], 
                     data['lower_ci'], 
                     data['upper_ci'], 
                     color=colors[i], alpha=0.2)
    
    # Add data point annotations
    for _, row in data.iterrows():
        plt.annotate(f"{row['blue_win_percentage']:.1f}%", 
                    (row['team_size_difference'], row['blue_win_percentage']),
                    textcoords="offset points", 
                    xytext=(0,10), 
                    ha='center',
                    fontsize=8)

# Add reference line for 50% win rate
plt.axhline(y=50, color='gray', linestyle='--', alpha=0.5)

# Styling
plt.grid(True, alpha=0.3, linestyle='--')
plt.xlabel('Team Size Difference (Blue - Red)', fontsize=12)
plt.ylabel('Blue Team Win Percentage (%)', fontsize=12)
plt.title('Blue Team Win Percentage by Team Size Difference\nControlled for Red Team Size with 95% Confidence Intervals', fontsize=14)

# Set y-axis limits with some padding
plt.ylim(0, 100)

# X-axis ticks for whole numbers
min_diff = results_df['team_size_difference'].min()
max_diff = results_df['team_size_difference'].max()
plt.xticks(range(int(min_diff), int(max_diff)+1))

# Add a legend
plt.legend(title='Controlled Variable', loc='best')

# Add a grid
plt.grid(True, linestyle='--', alpha=0.7)

# Add some contextual annotations
if len(red_team_sizes) > 0:
    # Add an explanation text box
    plt.figtext(0.5, 0.01, 
                "Note: Positive difference means Blue team is larger than Red team.\n"
                "Shaded areas represent 95% confidence intervals.\n"
                "Wide intervals reflect limited sample sizes in the experiments.",
                ha='center', fontsize=9, bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.2))

plt.tight_layout(rect=[0, 0.05, 1, 0.95])  # Adjust for the explanation text

# Save the plot
plot_file = 'blue_win_percentage_with_ci.png'
plt.savefig(plot_file, dpi=300, bbox_inches='tight')
print(f"Plot saved to {plot_file}")

# Print a summary table
print("\nDetailed Blue Win Percentage Table with CIs:")
# Create a prettier display format
summary_table = results_df.copy()
summary_table['CI'] = summary_table.apply(
    lambda row: f"({row['lower_ci']:.1f}%, {row['upper_ci']:.1f}%)", axis=1)
pivot_table = summary_table.pivot(index='red_team_size', 
                                 columns='team_size_difference',
                                 values=['blue_win_percentage', 'CI'])
print(pivot_table)
