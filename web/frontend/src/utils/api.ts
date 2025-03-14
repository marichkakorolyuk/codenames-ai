import axios from 'axios';

// Configure base API URL - update this in production
const API_BASE_URL = 'http://localhost:8000';

// API client
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Game related API functions
export const createGame = async (firstTeam?: string) => {
  const response = await api.post('/games', { first_team: firstTeam });
  return response.data;
};

export const getGame = async (gameId: string) => {
  const response = await api.get(`/games/${gameId}`);
  return response.data;
};

export const joinGame = async (gameId: string, playerName: string, team: string, role: string, aiControlled: boolean = false) => {
  const response = await api.post(`/games/${gameId}/join`, {
    game_id: gameId,
    player_name: playerName,
    team,
    role,
    ai_controlled: aiControlled
  });
  return response.data;
};

export const giveClue = async (gameId: string, playerId: string, clueWord: string, clueNumber: number) => {
  const response = await api.post(`/games/${gameId}/clue`, {
    game_id: gameId,
    player_id: playerId,
    clue_word: clueWord,
    clue_number: clueNumber
  });
  return response.data;
};

export const makeGuess = async (gameId: string, playerId: string, guessWord: string) => {
  const response = await api.post(`/games/${gameId}/guess`, {
    game_id: gameId,
    player_id: playerId,
    guess_word: guessWord
  });
  return response.data;
};

export const endTurn = async (gameId: string, playerId: string) => {
  const response = await api.post(`/games/${gameId}/end-turn`, {
    game_id: gameId,
    player_id: playerId
  });
  return response.data;
};

// WebSocket connection handler
export const connectToGameSocket = (playerId: string, onMessage: (data: any) => void) => {
  const socket = new WebSocket(`ws://localhost:8000/ws/${playerId}`);
  
  socket.onopen = () => {
    console.log('WebSocket connected');
  };
  
  socket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    onMessage(data);
  };
  
  socket.onerror = (error) => {
    console.error('WebSocket error:', error);
  };
  
  socket.onclose = () => {
    console.log('WebSocket disconnected');
  };
  
  return {
    close: () => socket.close(),
  };
};

export default api;
