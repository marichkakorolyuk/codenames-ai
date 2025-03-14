import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  Container,
  Divider,
  Flex,
  FormControl,
  FormLabel,
  Heading,
  Input,
  Radio,
  RadioGroup,
  Stack,
  Text,
  useToast,
  VStack,
  Switch,
  Checkbox,
  HStack,
} from '@chakra-ui/react';
import { createGame } from '../utils/api';

const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const toast = useToast();
  const [gameId, setGameId] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [useAI, setUseAI] = useState(false);
  const [openAIKey, setOpenAIKey] = useState('');
  const [showOpenAIInput, setShowOpenAIInput] = useState(false);
  
  // Red team setup
  const [redSpymasterType, setRedSpymasterType] = useState('human');
  const [redOperativeType, setRedOperativeType] = useState('human');
  const [redSpymasterName, setRedSpymasterName] = useState('Red Spymaster');
  const [redOperativeName, setRedOperativeName] = useState('Red Operative');
  
  // Blue team setup
  const [blueSpymasterType, setBlueSpymasterType] = useState('human');
  const [blueOperativeType, setBlueOperativeType] = useState('human');
  const [blueSpymasterName, setBlueSpymasterName] = useState('Blue Spymaster');
  const [blueOperativeName, setBlueOperativeName] = useState('Blue Operative');

  const handleAIToggleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const useAIPlayers = e.target.checked;
    setUseAI(useAIPlayers);
    if (useAIPlayers) {
      setShowOpenAIInput(true);
    } else {
      setShowOpenAIInput(false);
      setRedSpymasterType('human');
      setRedOperativeType('human');
      setBlueSpymasterType('human');
      setBlueOperativeType('human');
    }
  };

  const handleCreateGame = async () => {
    try {
      setIsLoading(true);
      // For this example, we'll pick a random first team
      const game = await createGame();
      
      // Store OpenAI key locally if provided
      if (openAIKey) {
        localStorage.setItem('codenames_openai_key', openAIKey);
      }
      
      // Store team setup info for the join page
      localStorage.setItem('codenames_red_spymaster_type', redSpymasterType);
      localStorage.setItem('codenames_red_operative_type', redOperativeType);
      localStorage.setItem('codenames_red_spymaster_name', redSpymasterName);
      localStorage.setItem('codenames_red_operative_name', redOperativeName);
      
      localStorage.setItem('codenames_blue_spymaster_type', blueSpymasterType);
      localStorage.setItem('codenames_blue_operative_type', blueOperativeType);
      localStorage.setItem('codenames_blue_spymaster_name', blueSpymasterName);
      localStorage.setItem('codenames_blue_operative_name', blueOperativeName);
      
      toast({
        title: 'Game created!',
        description: `Your game ID is: ${game.game_id}`,
        status: 'success',
        duration: 5000,
        isClosable: true,
      });
      
      navigate(`/join/${game.game_id}`);
    } catch (error) {
      console.error('Error creating game:', error);
      toast({
        title: 'Error creating game',
        description: 'Something went wrong. Please try again.',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleJoinGame = () => {
    if (!gameId.trim()) {
      toast({
        title: 'Game ID required',
        description: 'Please enter a game ID to join',
        status: 'warning',
        duration: 3000,
        isClosable: true,
      });
      return;
    }
    
    navigate(`/join/${gameId}`);
  };

  const renderPlayerTypeSelector = (teamColor: string, role: string, currentType: string, setType: (type: string) => void) => {
    if (!useAI) return null;
    
    return (
      <RadioGroup 
        onChange={setType} 
        value={currentType} 
        size="sm" 
        colorScheme={teamColor === 'red' ? 'red' : 'blue'}
      >
        <Stack direction="row">
          <Radio value="human">Human</Radio>
          <Radio value="ai">AI</Radio>
        </Stack>
      </RadioGroup>
    );
  };

  return (
    <Container maxW="container.md" py={10}>
      <VStack spacing={8} align="stretch">
        <Box textAlign="center">
          <Heading as="h1" size="2xl" mb={2} color="gray.700">
            Codenames
          </Heading>
          <Text fontSize="lg" color="gray.600">
            The word association spy game
          </Text>
        </Box>

        <Box bg="white" p={6} borderRadius="md" boxShadow="md">
          <Heading as="h2" size="lg" mb={4}>
            Create New Game
          </Heading>
          
          {/* AI Players Option */}
          <FormControl display="flex" alignItems="center" mb={6}>
            <FormLabel htmlFor="ai-players" mb="0">
              Use AI Players?
            </FormLabel>
            <Switch 
              id="ai-players" 
              isChecked={useAI}
              onChange={handleAIToggleChange} 
              colorScheme="purple"
            />
          </FormControl>
          
          {/* OpenAI API Key Input */}
          {showOpenAIInput && (
            <FormControl mb={6}>
              <FormLabel>OpenAI API Key (required for AI players)</FormLabel>
              <Input 
                type="password"
                placeholder="Enter your OpenAI API key" 
                value={openAIKey}
                onChange={(e) => setOpenAIKey(e.target.value)}
              />
              <Text fontSize="xs" mt={1} color="gray.500">
                Your API key is stored locally and used only for this game.
              </Text>
            </FormControl>
          )}
          
          <Divider mb={6} />
          
          {/* Team Setup Section */}
          <Heading as="h3" size="md" mb={4} color="gray.700">
            Team Setup
          </Heading>
          
          {/* Red Team Setup */}
          <Box 
            mb={6} 
            p={4} 
            bg="red.50" 
            borderRadius="md" 
            borderLeft="4px solid" 
            borderColor="red.500"
          >
            <Heading as="h4" size="sm" mb={3} color="red.700">
              RED TEAM
            </Heading>
            
            <VStack spacing={4} align="stretch">
              {/* Red Spymaster */}
              <Box>
                <HStack justifyContent="space-between" mb={2}>
                  <FormLabel mb={0} fontWeight="bold">Spymaster</FormLabel>
                  {renderPlayerTypeSelector('red', 'spymaster', redSpymasterType, setRedSpymasterType)}
                </HStack>
                {(redSpymasterType === 'human' || !useAI) && (
                  <Input 
                    size="sm"
                    placeholder="Enter name for Red Spymaster" 
                    value={redSpymasterName}
                    onChange={(e) => setRedSpymasterName(e.target.value)}
                  />
                )}
              </Box>
              
              {/* Red Operative */}
              <Box>
                <HStack justifyContent="space-between" mb={2}>
                  <FormLabel mb={0} fontWeight="bold">Operative</FormLabel>
                  {renderPlayerTypeSelector('red', 'operative', redOperativeType, setRedOperativeType)}
                </HStack>
                {(redOperativeType === 'human' || !useAI) && (
                  <Input 
                    size="sm"
                    placeholder="Enter name for Red Operative" 
                    value={redOperativeName}
                    onChange={(e) => setRedOperativeName(e.target.value)}
                  />
                )}
              </Box>
            </VStack>
          </Box>
          
          {/* Blue Team Setup */}
          <Box 
            mb={6} 
            p={4} 
            bg="blue.50" 
            borderRadius="md" 
            borderLeft="4px solid" 
            borderColor="blue.500"
          >
            <Heading as="h4" size="sm" mb={3} color="blue.700">
              BLUE TEAM
            </Heading>
            
            <VStack spacing={4} align="stretch">
              {/* Blue Spymaster */}
              <Box>
                <HStack justifyContent="space-between" mb={2}>
                  <FormLabel mb={0} fontWeight="bold">Spymaster</FormLabel>
                  {renderPlayerTypeSelector('blue', 'spymaster', blueSpymasterType, setBlueSpymasterType)}
                </HStack>
                {(blueSpymasterType === 'human' || !useAI) && (
                  <Input 
                    size="sm"
                    placeholder="Enter name for Blue Spymaster" 
                    value={blueSpymasterName}
                    onChange={(e) => setBlueSpymasterName(e.target.value)}
                  />
                )}
              </Box>
              
              {/* Blue Operative */}
              <Box>
                <HStack justifyContent="space-between" mb={2}>
                  <FormLabel mb={0} fontWeight="bold">Operative</FormLabel>
                  {renderPlayerTypeSelector('blue', 'operative', blueOperativeType, setBlueOperativeType)}
                </HStack>
                {(blueOperativeType === 'human' || !useAI) && (
                  <Input 
                    size="sm"
                    placeholder="Enter name for Blue Operative" 
                    value={blueOperativeName}
                    onChange={(e) => setBlueOperativeName(e.target.value)}
                  />
                )}
              </Box>
            </VStack>
          </Box>

          <Button 
            colorScheme="green" 
            width="full" 
            onClick={handleCreateGame}
            isLoading={isLoading}
            size="lg"
            mt={4}
          >
            Start Game
          </Button>
        </Box>

        <Divider />

        <Box bg="white" p={6} borderRadius="md" boxShadow="md">
          <Heading as="h2" size="lg" mb={4}>
            Join Existing Game
          </Heading>
          
          <Flex gap={4}>
            <FormControl flex={1}>
              <FormLabel>Game ID</FormLabel>
              <Input 
                placeholder="Enter game ID" 
                value={gameId}
                onChange={(e) => setGameId(e.target.value)}
              />
            </FormControl>
            
            <Button 
              colorScheme="blue" 
              alignSelf="flex-end"
              onClick={handleJoinGame}
            >
              Join Game
            </Button>
          </Flex>
        </Box>
      </VStack>
    </Container>
  );
};

export default HomePage;
