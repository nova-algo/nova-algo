import React from "react";
import {
  Box,
  VStack,
  Heading,
  Text,
  Container,
  useColorModeValue,
  SimpleGrid,
} from "@chakra-ui/react";
import { Link } from "@chakra-ui/next-js";
export default function Footer() {
  const textColor = useColorModeValue("gray.800", "gray.100");

  return (
    <Box bg={useColorModeValue("gray.100", "gray.800")} color={textColor}>
      <Container maxW="container.xl" py={10}>
        <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={8}>
          <VStack align="start">
            <Heading size="md" mb={2}>
              Nova Algo
            </Heading>
            <Text>Revolutionizing trading with AI-powered vaults</Text>
          </VStack>
          <VStack align="start">
            <Heading size="md" mb={2}>
              Quick Links
            </Heading>
            <Link href="#">About Us</Link>
            <Link href="/how-it-works">How It Works</Link>
            <Link href="/faqs">FAQ</Link>
          </VStack>
          <VStack align="start">
            <Heading size="md" mb={2}>
              Legal
            </Heading>
            <Link href="#">Terms of Service</Link>
            <Link href="#">Privacy Policy</Link>
          </VStack>
          <VStack align="start">
            <Heading size="md" mb={2}>
              Connect
            </Heading>
            <Link href="https://x.com/novaalgo" isExternal>
              Twitter
            </Link>
            <Link href="#" isExternal>
              LinkedIn
            </Link>
            <Link href="mailto:support@novaalgo.com" isExternal>
              Support
            </Link>
          </VStack>
        </SimpleGrid>
        <Text mt={10} textAlign="center">
          © 2024 Nova Algo. All rights reserved.
        </Text>
      </Container>
    </Box>
  );
}
