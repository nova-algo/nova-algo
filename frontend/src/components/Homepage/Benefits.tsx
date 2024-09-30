import React from "react";
import {
  Box,
  VStack,
  Heading,
  Text,
  Button,
  Container,
  useColorModeValue,
  Icon,
  Flex,
  Image,
} from "@chakra-ui/react";
import { motion, useScroll, useTransform } from "framer-motion";
import { FaChartLine } from "react-icons/fa";
import { Link } from "@chakra-ui/next-js";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const MotionBox = motion.create(Box as any);
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const MotionFlex = motion.create(Flex as any);

export default function Benefits() {
  const { scrollY } = useScroll();
  const opacity = useTransform(scrollY, [0, 200], [0, 1]);
  const benefits = [
    "Maximize returns through optimized automation",
    "Minimize risks with intelligent diversification",
    "Save time with full automation",
    "Stay ahead of the market with adaptive strategies",
  ];
  return (
    <MotionBox
      bg={useColorModeValue("blue.50", "blue.900")}
      py={20}
      style={{ opacity }}
    >
      <Container maxW="container.xl">
        <Flex
          direction={{ base: "column-reverse", lg: "row" }}
          alignItems="center"
          gap={5}
        >
          <Box flex={1} pr={{ base: 0, lg: 12 }} mb={{ base: 12, lg: 0 }}>
            <Heading as="h2" size="2xl" mb={6}>
              Unleash the Power of AI-Driven Trading Vaults
            </Heading>
            <Text fontSize="xl" mb={8}>
              Nova Algo&apos;s automated vaults bring institutional-grade
              technology to your fingertips, allowing you to:
            </Text>
            <VStack align="start" spacing={4}>
              {benefits.map((benefit, index) => (
                <MotionFlex
                  key={index}
                  alignItems="center"
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.5, delay: index * 0.1 }}
                >
                  <Icon as={FaChartLine} color="green.500" mr={2} />
                  <Text fontSize="lg">{benefit}</Text>
                </MotionFlex>
              ))}
            </VStack>
            <Link href={"/vaults"}>
              <Button
                as={motion.button}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                size="lg"
                colorScheme="blue"
                mt={8}
              >
                Explore Our Vaults
              </Button>
            </Link>
          </Box>
          <MotionBox
            flex={1}
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8 }}
          >
            {/* Placeholder for an image or animation */}
            <Box
              h={{ base: "auto", md: 400 }}
              w="100%"
              borderRadius="lg"
              maxW={{ lg: "none", md: 450 }}
            >
              <Image
                src="/images/Dashboard.png"
                alt="Vault"
                borderRadius={"lg"}
              />
            </Box>
          </MotionBox>
        </Flex>
      </Container>
    </MotionBox>
  );
}
