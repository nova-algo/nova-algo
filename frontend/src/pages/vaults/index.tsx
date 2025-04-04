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
  Flex,
} from "@chakra-ui/react";
import { motion } from "framer-motion";
import { Link } from "@chakra-ui/next-js";
import vaults from "@/lib/vaults.json";
import Header from "@/components/Header";
import { Vault } from "@/types";
import Head from "next/head";
import Footer from "@/components/Footer";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const MotionBox = motion.create(Box as any);
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const MotionButton = motion.create(Button as any);

const VaultsPage: React.FC = () => {
  const bgColor = useColorModeValue("gray.200", "gray.900");

  return (
    <>
      <Head>
        <title>Explore our advanced autmated vaults</title>
      </Head>
      <Header />
      <Box bg={bgColor} minHeight="100vh" py={12} mt={12}>
        <Container maxW="container.xl">
          <VStack spacing={8} align="stretch">
            <Heading as="h1" size="2xl" textAlign="center" mb={4}>
              Our Advanced Vaults
            </Heading>
            <Text fontSize="xl" textAlign="center" mb={8}>
              Explore our range of automated trading vaults, each powered by
              advanced algorithms.
            </Text>
            <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={10}>
              {vaults.map((vault) => (
                <VaultCard key={vault.id} vault={vault} />
              ))}
            </SimpleGrid>
          </VStack>
        </Container>
      </Box>
      <Footer />
    </>
  );
};
const VaultCard: React.FC<{ vault: Vault }> = ({ vault }) => {
  const cardBg = useColorModeValue("white", "gray.800");
  const textColor = useColorModeValue("gray.800", "white");

  return (
    <MotionBox
      whileHover={{ scale: 1.01 }}
      transition={{ duration: 0.3 }}
      bg={cardBg}
      borderRadius="3xl"
      overflow="hidden"
      boxShadow="lg"
    >
      <Box p={6} display="flex" flexDirection="column" height="100%">
        <VStack align="start" spacing={3} flex="1">
          <HStack>
            <Avatar size="md" src={vault?.avatar} />
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
          <Flex flex={1} align={"flex-end"}>
            <MotionButton
              as={Link}
              href={`/vaults/${vault.id}`}
              textDecor="none"
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.95 }}
              bgGradient="linear(to-r, #4A90E2, #9B59B6)"
              color="white"
              _hover={{
                bgGradient: "linear(to-r, #4A90E2, #9B59B6)",
              }}
              // mt="4"
              // w="100%"
            >
              Explore Vault
            </MotionButton>
          </Flex>
        </VStack>
      </Box>
    </MotionBox>
  );
};
export default VaultsPage;
