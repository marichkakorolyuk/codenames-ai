import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  Container,
  Flex,
  FormControl,
  FormLabel,
  Grid,
  Heading,
  Input,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  NumberIncrementStepper,
  NumberDecrementStepper,
  Text,
  VStack,
  HStack,
  Badge,
  Divider,
  useToast,
  useDisclosure,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  ModalCloseButton,
} from '@chakra-ui/react';
import { connectToGameSocket, giveClue, makeGuess, endTurn } from '../utils/api';
import GameCard from './GameCard';

interface Card {
  word: string;
  type: string | null;
  revealed: boolean;
}

const GamePage: React.FC = () => {
  const { gameId } = useParams<{ gameId: string }>();
  const navigate = useNavigate();
  const toast = useToast();
  const { isOpen, onOpen, onClose } = useDisclosure();
  
  // Player information
  const [playerId, setPlayerId] = useState('');
  const [playerName, setPlayerName] = useState('');
  const [playerTeam, setPlayerTeam] = useState('');
  const [playerRole, setPlayerRole] = useState('');
  
  // Game state
  const [gameState, setGameState] = useState<any>(null);
  const [board, setBoard] = useState<Card[]>([]);
  const [clueWord, setClueWord] = useState('');
  const [clueNumber, setClueNumber] = useState(1);
  const [currentClue, setCurrentClue] = useState<{ word: string, number: number } | null>(null);
  const [isMyTurn, setIsMyTurn] = useState(false);
  
  // Load player info from localStorage
  useEffect(() => {
    const storedPlayerId = localStorage.getItem('codenames_player_id');
    const storedPlayerName = localStorage.getItem('codenames_player_name');
    const storedPlayerTeam = localStorage.getItem('codenames_player_team');
    const storedPlayerRole = localStorage.getItem('codenames_player_role');
    
    if (!storedPlayerId || !storedPlayerTeam || !storedPlayerRole) {
      toast({
        title: 'Not joined',
        description: 'You need to join the game first',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
      navigate(`/join/${gameId}`);
      return;
    }
    
    setPlayerId(storedPlayerId);
    setPlayerName(storedPlayerName || 'Player');
    setPlayerTeam(storedPlayerTeam);
    setPlayerRole(storedPlayerRole);
  }, [gameId, navigate, toast]);
  
  // Check if it's the player's turn to act
  useEffect(() => {
    if (!gameState || !playerTeam) return;
    
    const myTurn = gameState.current_team === playerTeam;
    setIsMyTurn(myTurn);
    
    // Get current clue if available
    if (gameState.clue_history && gameState.clue_history.length > 0) {
      const lastClue = gameState.clue_history[gameState.clue_history.length - 1];
      setCurrentClue({ word: lastClue[1], number: lastClue[2] });
    } else {
      setCurrentClue(null);
    }
    
    // Check for AI players and simulate their moves
    if (gameState && gameState.players) {
      const openAIKey = localStorage.getItem('codenames_openai_key');
      if (openAIKey) {
        // Current team and role that should move
        const currentTeam = gameState.current_team;
        const currentRole = gameState.clue ? 'operative' : 'spymaster';
        
        // Find if the current player is an AI
        const currentAIPlayer = Object.values(gameState.players).find((p: any) => 
          p.team === currentTeam && 
          p.role === currentRole && 
          p.is_ai === true
        );
        
        if (currentAIPlayer) {
          // Prevent AI from taking its turn if this player is human (avoid duplicate moves)
          if (playerTeam === currentTeam && playerRole === currentRole) {
            return;
          }
          
          // Simulate AI thinking time
          const thinkingTime = currentRole === 'spymaster' ? 6000 : 3000;
          
          // Delay to simulate AI thinking
          setTimeout(async () => {
            try {
              // For spymaster, give a clue
              if (currentRole === 'spymaster') {
                // Simple AI logic: pick a random word and number between 1-3
                const teamWords = gameState.board
                  .filter((card: any) => !card.revealed && card.type === currentTeam)
                  .map((card: any) => card.word);
                
                if (teamWords.length > 0) {
                  // This is a very simple strategy - a real AI would use more sophisticated word connections
                  // In a real implementation, we'd use the OpenAI API to generate better clues
                  const clueWord = `clue-${Math.floor(Math.random() * 1000)}`;
                  const clueNumber = Math.min(Math.ceil(Math.random() * 3), teamWords.length);
                  
                  await giveClue(gameId || '', (currentAIPlayer as any).id, clueWord, clueNumber);
                }
              } 
              // For operative, make a guess
              else if (currentRole === 'operative') {
                // Simple AI strategy: randomly pick an unrevealed card
                const unrevealedCards = gameState.board.filter((card: any) => !card.revealed);
                
                if (unrevealedCards.length > 0) {
                  // In a real implementation, we'd use OpenAI to select cards based on the clue
                  const randomCard = unrevealedCards[Math.floor(Math.random() * unrevealedCards.length)];
                  await makeGuess(gameId || '', (currentAIPlayer as any).id, randomCard.word);
                }
              }
            } catch (error) {
              console.error('Error during AI move:', error);
            }
          }, thinkingTime);
        }
      }
    }
  }, [gameState, playerTeam, playerRole, gameId]);
  
  // Handle WebSocket messages
  const handleSocketMessage = useCallback((data: any) => {
    if (data.type === 'game_state_update') {
      setGameState(data.data);
      setBoard(data.data.board);
      
      // Check for game winner
      if (data.data.winner) {
        const winnerTeam = data.data.winner;
        toast({
          title: 'Game Over!',
          description: `The ${winnerTeam.toUpperCase()} team wins!`,
          status: winnerTeam === playerTeam ? 'success' : 'error',
          duration: null,
          isClosable: true,
        });
        onOpen(); // Open modal to show game over
      }
    }
  }, [onOpen, playerTeam, toast]);
  
  // Connect to WebSocket
  useEffect(() => {
    if (!playerId) return;
    
    const socketConnection = connectToGameSocket(playerId, handleSocketMessage);
    
    return () => {
      socketConnection.close();
    };
  }, [playerId, handleSocketMessage]);
  
  // Handle giving a clue (spymaster)
  const handleGiveClue = async () => {
    if (!clueWord.trim()) {
      toast({
        title: 'Clue required',
        description: 'Please enter a clue word',
        status: 'warning',
        duration: 3000,
        isClosable: true,
      });
      return;
    }
    
    try {
      await giveClue(gameId || '', playerId, clueWord, clueNumber);
      toast({
        title: 'Clue given',
        description: `You gave the clue "${clueWord}" for ${clueNumber}`,
        status: 'success',
        duration: 3000,
        isClosable: true,
      });
      setClueWord('');
    } catch (error) {
      console.error('Error giving clue:', error);
      toast({
        title: 'Error',
        description: 'Failed to give clue. Please try again.',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    }
  };
  
  // Handle making a guess (operative)
  const handleGuess = async (word: string) => {
    try {
      const result = await makeGuess(gameId || '', playerId, word);
      
      const cardType = result.card_type;
      const isCorrect = (playerTeam === 'red' && cardType === 'red') || 
                        (playerTeam === 'blue' && cardType === 'blue');
      
      toast({
        title: isCorrect ? 'Correct!' : 'Incorrect!',
        description: `"${word}" is a ${cardType.toUpperCase()} card`,
        status: isCorrect ? 'success' : 'warning',
        duration: 3000,
        isClosable: true,
      });
      
      if (result.game_over) {
        // Game over handling is done via WebSocket state update
      }
    } catch (error) {
      console.error('Error making guess:', error);
      toast({
        title: 'Error',
        description: 'Failed to make guess. Please try again.',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    }
  };
  
  // Handle ending turn
  const handleEndTurn = async () => {
    try {
      await endTurn(gameId || '', playerId);
      toast({
        title: 'Turn ended',
        description: 'You ended your team\'s turn',
        status: 'info',
        duration: 3000,
        isClosable: true,
      });
    } catch (error) {
      console.error('Error ending turn:', error);
      toast({
        title: 'Error',
        description: 'Failed to end turn. Please try again.',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    }
  };
  
  // Return to home
  const handleReturnToHome = () => {
    navigate('/');
  };
  
  // Get player description
  const getPlayerDescription = () => {
    return `${playerName} (${playerTeam.toUpperCase()} ${playerRole})`;
  };
  
  // Get turn instruction
  const getTurnInstruction = () => {
    if (!gameState) return '';
    
    if (gameState.winner) {
      return `Game Over! ${gameState.winner.toUpperCase()} team wins!`;
    }
    
    const currentTeam = gameState.current_team;
    
    if (isMyTurn) {
      if (playerRole === 'spymaster' && (!currentClue || currentClue.word === '')) {
        return 'Your turn to give a clue!';
      } else if (playerRole === 'operative') {
        return 'Your turn to guess!';
      }
    }
    
    return `Waiting for ${currentTeam.toUpperCase()} team to ${currentClue ? 'guess' : 'give a clue'}`;
  };
  
  return (
    <Container maxW="container.xl" py={4}>
      <VStack spacing={4} align="stretch">
        <Flex justifyContent="space-between" alignItems="center">
          <Heading size="lg" color="gray.700">
            Codenames Game
          </Heading>
          <HStack>
            <Text fontWeight="bold">{getPlayerDescription()}</Text>
            <Badge colorScheme={playerTeam === 'red' ? 'red' : 'blue'}>
              {playerTeam.toUpperCase()}
            </Badge>
            <Badge>{playerRole}</Badge>
          </HStack>
        </Flex>
        
        {gameState && (
          <Box bg="white" p={4} borderRadius="md" boxShadow="sm">
            <Flex justifyContent="space-between" alignItems="center">
              <HStack>
                <Badge colorScheme="red" fontSize="md" p={2}>
                  Red: {gameState.red_remaining} left
                </Badge>
                <Badge colorScheme="blue" fontSize="md" p={2}>
                  Blue: {gameState.blue_remaining} left
                </Badge>
              </HStack>
              
              <Box>
                <Text fontWeight="bold">
                  Current Turn: <Badge colorScheme={gameState.current_team === 'red' ? 'red' : 'blue'} fontSize="md">
                    {gameState.current_team.toUpperCase()}
                  </Badge>
                </Text>
                <Text color="gray.600" fontStyle="italic">
                  {getTurnInstruction()}
                </Text>
              </Box>
              
              {isMyTurn && playerRole === 'operative' && (
                <Button colorScheme="orange" size="sm" onClick={handleEndTurn}>
                  End Turn
                </Button>
              )}
            </Flex>
          </Box>
        )}
        
        {currentClue && (
          <Box bg="gray.100" p={3} borderRadius="md">
            <Text fontSize="lg" fontWeight="bold" textAlign="center">
              Current Clue: <Badge colorScheme="purple" fontSize="lg">{currentClue.word}</Badge> for {currentClue.number}
            </Text>
          </Box>
        )}
        
        {/* Spymaster Clue Input */}
        {isMyTurn && playerRole === 'spymaster' && !currentClue && (
          <Box bg="white" p={4} borderRadius="md" boxShadow="sm">
            <Heading size="sm" mb={3}>Give a Clue</Heading>
            <Flex gap={4}>
              <FormControl>
                <FormLabel>Clue Word</FormLabel>
                <Input 
                  placeholder="Enter a one-word clue" 
                  value={clueWord}
                  onChange={(e) => setClueWord(e.target.value)}
                />
              </FormControl>
              
              <FormControl width="150px">
                <FormLabel>Number</FormLabel>
                <NumberInput min={0} max={9} value={clueNumber} onChange={(_, value) => setClueNumber(value)}>
                  <NumberInputField />
                  <NumberInputStepper>
                    <NumberIncrementStepper />
                    <NumberDecrementStepper />
                  </NumberInputStepper>
                </NumberInput>
              </FormControl>
              
              <Button colorScheme="blue" alignSelf="flex-end" onClick={handleGiveClue}>
                Give Clue
              </Button>
            </Flex>
          </Box>
        )}
        
        {/* Game Board */}
        <Box bg="white" p={4} borderRadius="md" boxShadow="md">
          <Heading size="md" mb={4}>Game Board</Heading>
          <Grid templateColumns="repeat(5, 1fr)" gap={3}>
            {board.map((card, index) => (
              <GameCard 
                key={index}
                word={card.word}
                type={card.type}
                revealed={card.revealed}
                isSelectable={isMyTurn && playerRole === 'operative' && !card.revealed}
                onSelect={() => handleGuess(card.word)}
              />
            ))}
          </Grid>
        </Box>
        
        {/* Game History */}
        {gameState && gameState.clue_history && gameState.clue_history.length > 0 && (
          <Box bg="white" p={4} borderRadius="md" boxShadow="sm">
            <Heading size="sm" mb={3}>Game History</Heading>
            <VStack align="stretch" spacing={2} maxH="200px" overflowY="auto">
              {gameState.clue_history.map((clue: [string, string, number], i: number) => (
                <Box key={i} p={2} bg="gray.50" borderRadius="md">
                  <Text>
                    <Badge colorScheme={clue[0] === 'red' ? 'red' : 'blue'}>
                      {clue[0].toUpperCase()}
                    </Badge>
                    {' '} Spymaster: "{clue[1]}" for {clue[2]}
                  </Text>
                </Box>
              ))}
            </VStack>
          </Box>
        )}
      </VStack>
      
      {/* Game Over Modal */}
      <Modal isOpen={isOpen} onClose={onClose} isCentered>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Game Over!</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            {gameState && gameState.winner && (
              <VStack spacing={4}>
                <Heading size="lg" textAlign="center">
                  {gameState.winner.toUpperCase()} Team Wins!
                </Heading>
                <Badge 
                  colorScheme={gameState.winner === 'red' ? 'red' : 'blue'} 
                  fontSize="2xl" 
                  p={2}
                >
                  {gameState.winner === 'red' ? 'RED' : 'BLUE'} VICTORY
                </Badge>
                <Text>Would you like to play another game?</Text>
              </VStack>
            )}
          </ModalBody>
          <ModalFooter>
            <Button colorScheme="blue" mr={3} onClick={handleReturnToHome}>
              Return to Home
            </Button>
            <Button variant="ghost" onClick={onClose}>Close</Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Container>
  );
};

export default GamePage;
