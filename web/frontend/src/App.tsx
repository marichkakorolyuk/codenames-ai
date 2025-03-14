import React from 'react';
import {
  ChakraProvider,
  Box,
  extendTheme,
} from '@chakra-ui/react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

// Components
import HomePage from './components/HomePage';
import GamePage from './components/GamePage';
import JoinGamePage from './components/JoinGamePage';

// Custom theme
const theme = extendTheme({
  colors: {
    brand: {
      red: '#ff4d4d',
      blue: '#4d94ff',
      neutral: '#e0dcc5',
      assassin: '#2d2d2d',
      cardBack: '#faf0e6',
    },
  },
  styles: {
    global: {
      body: {
        bg: '#f9f9f9',
        color: 'gray.800',
      },
    },
  },
});

function App() {
  return (
    <ChakraProvider theme={theme}>
      <Router>
        <Box minH="100vh" p={4}>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/join/:gameId" element={<JoinGamePage />} />
            <Route path="/game/:gameId" element={<GamePage />} />
          </Routes>
        </Box>
      </Router>
    </ChakraProvider>
  );
}

export default App;
