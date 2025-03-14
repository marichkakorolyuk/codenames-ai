import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  Container,
  FormControl,
  FormLabel,
  Heading,
  Input,
  Radio,
  RadioGroup,
  Stack,
  Switch,
  Text,
  useToast,
  VStack,
  Grid,
  GridItem,
  HStack,
  Badge,
} from '@chakra-ui/react';
import { getGame, joinGame } from '../utils/api';

interface Player {
  id: string;
  name: string;
  team: string;
  role: string;
  ai_controlled: boolean;
}

const JoinGamePage: React.FC = () => {
  const { gameId } = useParams<{ gameId: string }>();
  const navigate = useNavigate();
  const toast = useToast();

  const [playerName, setPlayerName] = useState('');
  const [team, setTeam] = useState('red');
  const [role, setRole] = useState('operative');
  const [isAI, setIsAI] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [gameInfo, setGameInfo] = useState<any>(null);
  const [players, setPlayers] = useState<Player[]>([]);

  // Fetch game information
  useEffect(() => {
    const fetchGameInfo = async () => {
      try {
        if (!gameId) return;
        
        const data = await getGame(gameId);
        setGameInfo(data);
        
        // Convert players object to array
        const playerArray = Object.values(data.players || {}) as Player[];
        setPlayers(playerArray);
        
        // Check for stored team setup
        const storedRedSpymasterType = localStorage.getItem('codenames_red_spymaster_type');
        const storedRedOperativeType = localStorage.getItem('codenames_red_operative_type');
        const storedBlueSpymasterType = localStorage.getItem('codenames_blue_spymaster_type');
        const storedBlueOperativeType = localStorage.getItem('codenames_blue_operative_type');
        
        // If this is a new game with pre-configured team setup, join AI players automatically
        if (playerArray.length === 0 && (
          storedRedSpymasterType === 'ai' || 
          storedRedOperativeType === 'ai' || 
          storedBlueSpymasterType === 'ai' || 
          storedBlueOperativeType === 'ai'
        )) {
          // Join AI players automatically
          if (storedRedSpymasterType === 'ai') {
            const name = localStorage.getItem('codenames_red_spymaster_name') || 'Red Spymaster';
            await joinGame(gameId, name, 'red', 'spymaster', true);
          }
          
          if (storedRedOperativeType === 'ai') {
            const name = localStorage.getItem('codenames_red_operative_name') || 'Red Operative';
            await joinGame(gameId, name, 'red', 'operative', true);
          }
          
          if (storedBlueSpymasterType === 'ai') {
            const name = localStorage.getItem('codenames_blue_spymaster_name') || 'Blue Spymaster';
            await joinGame(gameId, name, 'blue', 'spymaster', true);
          }
          
          if (storedBlueOperativeType === 'ai') {
            const name = localStorage.getItem('codenames_blue_operative_name') || 'Blue Operative';
            await joinGame(gameId, name, 'blue', 'operative', true);
          }
          
          // Refresh player list after AI players join
          setTimeout(fetchGameInfo, 1000);
        }
      } catch (error) {
        console.error('Error fetching game:', error);
        toast({
          title: 'Error',
          description: 'Could not fetch game information. The game may not exist.',
          status: 'error',
          duration: 5000,
          isClosable: true,
        });
      }
    };

    fetchGameInfo();
    
    // Refresh game info every 3 seconds
    const interval = setInterval(fetchGameInfo, 3000);
    return () => clearInterval(interval);
  }, [gameId, toast]);

  // Check if role is already taken
  const isRoleTaken = (teamValue: string, roleValue: string) => {
    return players.some(
      (player) => player.team === teamValue && player.role === roleValue
    );
  };
  
  // Suggest a role based on what's available and stored preferences
  useEffect(() => {
    if (players.length > 0) {
      // Find available roles
      const takenPositions = players.map(p => `${p.team}-${p.role}`);
      const availableRoles = [
        {team: 'red', role: 'spymaster'},
        {team: 'red', role: 'operative'},
        {team: 'blue', role: 'spymaster'},
        {team: 'blue', role: 'operative'}
      ].filter(pos => !takenPositions.includes(`${pos.team}-${pos.role}`));
      
      if (availableRoles.length > 0) {
        // Check stored preferences for human roles
        const redSpymasterType = localStorage.getItem('codenames_red_spymaster_type');
        const redOperativeType = localStorage.getItem('codenames_red_operative_type');
        const blueSpymasterType = localStorage.getItem('codenames_blue_spymaster_type');
        const blueOperativeType = localStorage.getItem('codenames_blue_operative_type');
        
        // Find first available human role based on stored preferences
        const humanRolePreference = availableRoles.find(pos => {
          if (pos.team === 'red' && pos.role === 'spymaster') {
            return redSpymasterType === 'human' || !redSpymasterType;
          } else if (pos.team === 'red' && pos.role === 'operative') {
            return redOperativeType === 'human' || !redOperativeType;
          } else if (pos.team === 'blue' && pos.role === 'spymaster') {
            return blueSpymasterType === 'human' || !blueSpymasterType;
          } else if (pos.team === 'blue' && pos.role === 'operative') {
            return blueOperativeType === 'human' || !blueOperativeType;
          }
          return true;
        });
        
        if (humanRolePreference) {
          setTeam(humanRolePreference.team);
          setRole(humanRolePreference.role);
          
          // Set player name based on stored name
          const nameKey = `codenames_${humanRolePreference.team}_${humanRolePreference.role}_name`;
          const storedName = localStorage.getItem(nameKey);
          if (storedName && storedName.includes('Spymaster') || storedName?.includes('Operative')) {
            // Only use a generic stored name if it's a user's custom name
            setPlayerName('');
          } else if (storedName) {
            setPlayerName(storedName);
          }
        }
      }
    }
  }, [players]);

  const handleJoinGame = async () => {
    if (!playerName.trim()) {
      toast({
        title: 'Name required',
        description: 'Please enter your name',
        status: 'warning',
        duration: 3000,
        isClosable: true,
      });
      return;
    }

    // Check if the selected role is already taken
    if (isRoleTaken(team, role)) {
      toast({
        title: 'Role already taken',
        description: `The ${role} role for the ${team} team is already taken`,
        status: 'warning',
        duration: 3000,
        isClosable: true,
      });
      return;
    }

    try {
      setIsLoading(true);
      const player = await joinGame(gameId || '', playerName, team, role, isAI);
      
      // Store player ID for game session
      localStorage.setItem('codenames_player_id', player.player_id);
      localStorage.setItem('codenames_player_name', player.name);
      localStorage.setItem('codenames_player_team', player.team);
      localStorage.setItem('codenames_player_role', player.role);
      
      toast({
        title: 'Joined game!',
        description: `You have joined as ${team} team ${role}`,
        status: 'success',
        duration: 5000,
        isClosable: true,
      });
      
      navigate(`/game/${gameId}`);
    } catch (error) {
      console.error('Error joining game:', error);
      toast({
        title: 'Error joining game',
        description: 'Something went wrong. Please try again.',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Container maxW="container.md" py={10}>
      <VStack spacing={8} align="stretch">
        <Box textAlign="center">
          <Heading as="h1" size="xl" mb={2} color="gray.700">
            Join Game
          </Heading>
          {gameInfo && (
            <Text fontSize="md" color="gray.600">
              Game ID: <Badge colorScheme="blue">{gameId}</Badge> | 
              Current Team: <Badge colorScheme={gameInfo.current_team === 'red' ? 'red' : 'blue'}>
                {gameInfo.current_team?.toUpperCase()}
              </Badge>
            </Text>
          )}
        </Box>

        <Box bg="white" p={6} borderRadius="md" boxShadow="md">
          <Heading as="h2" size="md" mb={4}>
            Current Players:
          </Heading>
          
          {players.length === 0 ? (
            <Text color="gray.500">No players have joined yet</Text>
          ) : (
            <Grid templateColumns="repeat(2, 1fr)" gap={4}>
              {/* Red Team */}
              <GridItem colSpan={1} bg="red.50" p={3} borderRadius="md">
                <Heading size="sm" color="red.600" mb={2}>
                  Red Team
                </Heading>
                {players
                  .filter(player => player.team === 'red')
                  .map(player => (
                    <HStack key={player.id} mb={2}>
                      <Text fontWeight="bold">{player.name}</Text>
                      <Badge>{player.role}</Badge>
                      {player.ai_controlled && <Badge colorScheme="purple">AI</Badge>}
                    </HStack>
                  ))}
              </GridItem>
              
              {/* Blue Team */}
              <GridItem colSpan={1} bg="blue.50" p={3} borderRadius="md">
                <Heading size="sm" color="blue.600" mb={2}>
                  Blue Team
                </Heading>
                {players
                  .filter(player => player.team === 'blue')
                  .map(player => (
                    <HStack key={player.id} mb={2}>
                      <Text fontWeight="bold">{player.name}</Text>
                      <Badge>{player.role}</Badge>
                      {player.ai_controlled && <Badge colorScheme="purple">AI</Badge>}
                    </HStack>
                  ))}
              </GridItem>
            </Grid>
          )}
        </Box>

        <Box bg="white" p={6} borderRadius="md" boxShadow="md">
          <Heading as="h2" size="lg" mb={4}>
            Join This Game
          </Heading>
          
          <FormControl mb={4}>
            <FormLabel>Your Name</FormLabel>
            <Input 
              placeholder="Enter your name" 
              value={playerName}
              onChange={(e) => setPlayerName(e.target.value)}
            />
          </FormControl>
          
          <FormControl mb={4}>
            <FormLabel>Team</FormLabel>
            <RadioGroup onChange={setTeam} value={team}>
              <Stack direction="row">
                <Radio value="red" colorScheme="red">Red Team</Radio>
                <Radio value="blue" colorScheme="blue">Blue Team</Radio>
              </Stack>
            </RadioGroup>
          </FormControl>
          
          <FormControl mb={4}>
            <FormLabel>Role</FormLabel>
            <RadioGroup onChange={setRole} value={role}>
              <Stack direction="row">
                <Radio value="spymaster">Spymaster</Radio>
                <Radio value="operative">Operative</Radio>
              </Stack>
            </RadioGroup>
          </FormControl>
          
          <FormControl display="flex" alignItems="center" mb={6}>
            <FormLabel htmlFor="ai-player" mb="0">
              AI Player?
            </FormLabel>
            <Switch 
              id="ai-player" 
              isChecked={isAI}
              onChange={(e) => setIsAI(e.target.checked)} 
            />
          </FormControl>

          <Button 
            colorScheme="green" 
            width="full" 
            onClick={handleJoinGame}
            isLoading={isLoading}
          >
            Join Game
          </Button>
        </Box>
      </VStack>
    </Container>
  );
};

export default JoinGamePage;
