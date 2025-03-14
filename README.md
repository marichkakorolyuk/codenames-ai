# Codenames Terminal Game

A terminal-based implementation of the Codenames board game with support for both human and AI players using the OpenAI API.

## Game Overview

Codenames is a game for two teams (Red and Blue) with a grid of 25 words. Some words belong to the Red Team, some to the Blue Team, some are neutral, and one is the Assassin. Each team has a Spymaster who knows which words belong to which team. The Spymasters take turns giving one-word clues to help their team's Operatives guess the correct words. The team that guesses all their words first wins.

## Features

- Play the game through a terminal interface
- Support for both human and AI players using OpenAI's API
- Flexible configuration: play human vs human, human vs AI, or AI vs AI
- Each team consists of a Spymaster and Operatives

## Getting Started

### Prerequisites

- Python 3.6+
- OpenAI API key (required for AI players)

### Installation

1. Clone this repository or download the code
2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

### Running the Game

1. Set your OpenAI API key as an environment variable (optional):
   ```
   export OPENAI_API_KEY="your-api-key-here"
   ```
   
   Alternatively, you can enter your API key when prompted during game setup.

2. Run the game:
   ```
   python terminal_game.py
   ```

3. Follow the on-screen instructions to set up teams and play the game.

## Gameplay Instructions

1. During setup, choose human or AI players for each role (Spymaster and Operative) on each team.
2. The Spymaster provides a one-word clue followed by a number indicating how many words on the board relate to that clue.
3. Operatives try to guess words based on the clue. They can make up to N+1 guesses, where N is the number given with the clue.
4. The turn ends when the Operative guesses incorrectly, chooses to end their turn, or runs out of guesses.
5. The game ends when one team guesses all their words or when a team guesses the Assassin word (and loses).

## Future Development

In the future, this game will also support a web-based UI for a more interactive experience.

## License

This project is open-source and available under the MIT License.
