import React from 'react';
import { Box, Text } from '@chakra-ui/react';

interface GameCardProps {
  word: string;
  type: string | null;
  revealed: boolean;
  isSelectable?: boolean;
  onSelect?: () => void;
}

const GameCard: React.FC<GameCardProps> = ({ 
  word, 
  type, 
  revealed, 
  isSelectable = false,
  onSelect
}) => {
  // Get card background color based on type and revealed state
  const getCardBgColor = () => {
    if (!revealed) return 'brand.cardBack';
    
    switch (type) {
      case 'red':
        return 'brand.red';
      case 'blue':
        return 'brand.blue';
      case 'neutral':
        return 'brand.neutral';
      case 'assassin':
        return 'brand.assassin';
      default:
        return 'brand.cardBack';
    }
  };
  
  // Get text color based on card type and revealed state
  const getTextColor = () => {
    if (!revealed) return 'gray.800';
    
    return type === 'assassin' ? 'white' : 'gray.800';
  };
  
  // Handle card click
  const handleClick = () => {
    if (isSelectable && onSelect) {
      onSelect();
    }
  };
  
  return (
    <Box
      height="100px"
      borderRadius="md"
      border="1px solid"
      borderColor="gray.300"
      bg={getCardBgColor()}
      color={getTextColor()}
      display="flex"
      justifyContent="center"
      alignItems="center"
      textAlign="center"
      cursor={isSelectable ? 'pointer' : 'default'}
      transition="all 0.2s"
      _hover={{
        transform: isSelectable ? 'translateY(-2px)' : 'none',
        boxShadow: isSelectable ? 'md' : 'none',
      }}
      onClick={handleClick}
    >
      <Text 
        fontWeight="bold"
        fontSize="lg"
        px={2}
        textTransform="uppercase"
      >
        {word}
      </Text>
    </Box>
  );
};

export default GameCard;
