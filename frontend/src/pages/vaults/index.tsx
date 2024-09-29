import React from "react";
import {
  Box,
  Container,
  SimpleGrid,
  Heading,
  Text,
  Button,
  VStack,
  useColorModeValue,
  HStack,
  Avatar,
  Stack,
} from "@chakra-ui/react";
import { motion } from "framer-motion";
import { Link } from "@chakra-ui/next-js";
import { Vault, vaults } from "@/lib/vaults";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const MotionBox = motion.create(Box as any);
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const MotionButton = motion.create(Button as any);

const VaultCard: React.FC<{ vault: Vault }> = ({ vault }) => {
  const cardBg = useColorModeValue("white", "gray.800");
  const textColor = useColorModeValue("gray.800", "white");

  return (
    <MotionBox
      whileHover={{ scale: 1.05 }}
      transition={{ duration: 0.3 }}
      bg={cardBg}
      borderRadius="3xl"
      overflow="hidden"
      boxShadow="lg"
    >
      <Box p={6}>
        <VStack align="start" spacing={3}>
          <HStack>
            <Avatar size="md" src="https://bit.ly/dan-abramov" />
            <Heading as="h3" size="lg" color={textColor}>
              {vault.name}
            </Heading>
          </HStack>
          <Text color={textColor}>{vault.description}</Text>

          <Text fontWeight="bold" color="green.500">
            {vault.performance}
          </Text>

          <HStack wrap="wrap" justify="space-between" w={"full"} gap={4}>
            <Stack>
              <Text>Deposit Tokens</Text>
              <HStack wrap="wrap">
                {vault.depositTokens.map((token) => (
                  <Avatar
                    key={token.name}
                    size="xs"
                    src={token.image}
                    name={token.name}
                  />
                ))}
              </HStack>
            </Stack>
            <Stack>
              <Text>Trading Tokens</Text>
              <HStack wrap="wrap">
                {vault.tradingTokens.map((token) => (
                  <Avatar
                    key={token.name}
                    size="xs"
                    src={token.image}
                    name={token.name}
                  />
                ))}
              </HStack>
            </Stack>
          </HStack>
          <Link href={`/vaults/${vault.id}`} style={{ textDecoration: "none" }}>
            <MotionButton
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.95 }}
              bgGradient="linear(to-r, #4A90E2, #9B59B6)"
              color="white"
              _hover={{
                bgGradient: "linear(to-r, #4A90E2, #9B59B6)",
                opacity: 0.9,
              }}
            >
              Explore Vault
            </MotionButton>
          </Link>
        </VStack>
      </Box>
    </MotionBox>
  );
};

const VaultsPage: React.FC = () => {
  const bgColor = useColorModeValue("gray.100", "gray.900");

  return (
    <Box bg={bgColor} minHeight="100vh" py={12}>
      <Container maxW="container.xl">
        <VStack spacing={8} align="stretch">
          <Heading as="h1" size="2xl" textAlign="center" mb={4}>
            Our AI-Powered Vaults
          </Heading>
          <Text fontSize="xl" textAlign="center" mb={8}>
            Explore our range of automated trading vaults, each powered by
            advanced AI algorithms.
          </Text>
          <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={10}>
            {vaults.map((vault) => (
              <VaultCard key={vault.id} vault={vault} />
            ))}
          </SimpleGrid>
        </VStack>
      </Container>
    </Box>
  );
};

export default VaultsPage;
