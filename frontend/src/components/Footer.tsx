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
            <Text as="a" href="#">
              About Us
            </Text>
            <Text as="a" href="#">
              How It Works
            </Text>
            <Text as="a" href="#">
              FAQ
            </Text>
          </VStack>
          <VStack align="start">
            <Heading size="md" mb={2}>
              Legal
            </Heading>
            <Text as="a" href="#">
              Terms of Service
            </Text>
            <Text as="a" href="#">
              Privacy Policy
            </Text>
          </VStack>
          <VStack align="start">
            <Heading size="md" mb={2}>
              Connect
            </Heading>
            <Text as="a" href="#">
              Twitter
            </Text>
            <Text as="a" href="#">
              LinkedIn
            </Text>
            <Text as="a" href="#">
              Support
            </Text>
          </VStack>
        </SimpleGrid>
        <Text mt={10} textAlign="center">
          © 2024 Nova Algo. All rights reserved.
        </Text>
      </Container>
    </Box>
  );
}
