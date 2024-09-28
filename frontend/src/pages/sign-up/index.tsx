import React from "react";
import {
  Box,
  Button,
  Container,
  Flex,
  Heading,
  Text,
  VStack,
  Image,
  Divider,
  useColorModeValue,
} from "@chakra-ui/react";
import { FaGoogle, FaWallet } from "react-icons/fa";
import { motion } from "framer-motion";

const MotionBox = motion.create(Box);

const SignUpPage: React.FC = () => {
  const bgColor = useColorModeValue("gray.50", "gray.900");
  const textColor = useColorModeValue("gray.800", "gray.100");
  const dividerColor = useColorModeValue("gray.300", "gray.600");

  return (
    <Container maxW="container.xl" p={0}>
      <Flex
        h={{ base: "auto", md: "100vh" }}
        py={[0, 10, 20]}
        direction={{ base: "column-reverse", md: "row" }}
      >
        {/* Left side with illustration */}
        <MotionBox
          initial={{ opacity: 0, x: -50 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5 }}
          w={{ base: "full", md: "50%" }}
          h={{ base: "200px", md: "full" }}
          bgGradient="linear(to-r, blue.400, purple.500)"
          borderRadius={{ base: "md", md: "15px 0 0 15px" }}
          overflow="hidden"
          position="relative"
        >
          <Image
            src="/api/placeholder/800/600"
            alt="Sign up illustration"
            objectFit="cover"
            w="full"
            h="full"
          />
          <Box
            position="absolute"
            bottom="8"
            left="8"
            color="white"
            fontWeight="bold"
            fontSize="xl"
            textShadow="1px 1px 3px rgba(0,0,0,0.3)"
          >
            Join Nova Algo Today
          </Box>
        </MotionBox>

        {/* Right side with sign-up form */}
        <MotionBox
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          w={{ base: "full", md: "50%" }}
          h="full"
          bg={bgColor}
          p={10}
          borderRadius={{ base: "md", md: "0 15px 15px 0" }}
          boxShadow="xl"
        >
          <VStack spacing={8} align="stretch">
            <Box>
              <Heading as="h1" size="2xl" mb={3} color={textColor}>
                Get Started
              </Heading>
              <Text fontSize="xl" color={textColor}>
                Join thousands of traders using AI-powered automated vaults to
                optimize their portfolios.
              </Text>
            </Box>

            <VStack spacing={4}>
              <Button
                leftIcon={<FaWallet />}
                colorScheme="blue"
                size="lg"
                w="full"
                fontSize="md"
              >
                Connect Wallet
              </Button>
              <Button
                leftIcon={<FaGoogle />}
                colorScheme="red"
                variant="outline"
                size="lg"
                w="full"
                fontSize="md"
              >
                Continue with Google
              </Button>
            </VStack>

            <Flex align="center">
              <Divider borderColor={dividerColor} />
              <Text px={4} color={textColor} fontWeight="medium">
                or
              </Text>
              <Divider borderColor={dividerColor} />
            </Flex>

            <VStack spacing={4}>
              <Text color={textColor} fontSize="lg" textAlign="center">
                Sign up with your email to get started
              </Text>
              <Button colorScheme="purple" size="lg" w="full" fontSize="md">
                Sign Up with Email
              </Button>
            </VStack>

            <Text color={textColor} fontSize="sm" textAlign="center">
              By signing up, you agree to our Terms of Service and Privacy
              Policy.
            </Text>
          </VStack>
        </MotionBox>
      </Flex>
    </Container>
  );
};

export default SignUpPage;
