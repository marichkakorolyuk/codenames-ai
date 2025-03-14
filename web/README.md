# Codenames Web Application

A web-based implementation of the Codenames board game with FastAPI backend and React frontend.

## Features

- Create and join games
- Two teams (Red and Blue)
- Support for AI or human players
- Real-time game updates through WebSockets
- Responsive UI with Chakra UI

## Setup and Installation

### Prerequisites

- Python 3.7+ (for backend)
- Node.js and npm (for frontend)

### Backend Setup

1. Navigate to the root directory of the project:

```bash
cd /path/to/codenames
```

2. Install required Python packages:

```bash
pip install -r requirements.txt
```

3. Start the FastAPI server:

```bash
cd web/backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

1. Navigate to the frontend directory:

```bash
cd /path/to/codenames/web/frontend
```

2. Install Node.js dependencies:

```bash
npm install
```

3. Start the React development server:

```bash
npm start
```

## How to Play

1. Open your browser and navigate to http://localhost:3000
2. Create a new game or join an existing game with a Game ID
3. Select your team (Red or Blue) and role (Spymaster or Operative)
4. Share the Game ID with other players so they can join
5. Play according to the standard Codenames rules:
   - Spymasters take turns giving clues
   - Operatives try to guess the cards based on clues
   - The first team to reveal all their cards wins

## Game Rules

### Roles

- **Spymaster**: Gives one-word clues to help their team guess the right cards
- **Operative**: Guesses cards based on the clue given by their Spymaster

### Gameplay

1. The Spymaster provides a one-word clue and a number, indicating how many cards are related to that clue
2. The Operatives discuss and select cards they believe match the clue
3. If the Operatives select a card of their team's color, they can continue guessing
4. If they select a neutral card or a card of the opposing team, their turn ends
5. If they select the Assassin card, they lose immediately
6. The team that reveals all their cards first wins

## API Documentation

API documentation is available at http://localhost:8000/docs when the backend server is running.

## License

This project is open source and available under the MIT license.
