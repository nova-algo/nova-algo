import { Link } from "@chakra-ui/next-js";
import {
  Box,
  VStack,
  Heading,
  Text,
  Button,
  Container,
  useColorModeValue,
  HStack,
} from "@chakra-ui/react";
import { motion } from "framer-motion";
import { LuArrowRight } from "react-icons/lu";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const MotionBox = motion.create(Box as any);
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const MotionButton = motion.create(Button as any, { forwardMotionProps: true });
const Hero = () => {
  const textColor = useColorModeValue("gray.800", "gray.100");

  return (
    <Box pos={"relative"}>
      {/* Background blobs */}
      <MotionBox
        position="absolute"
        top="-10%"
        left="-5%"
        w="30%"
        h="30%"
        borderRadius="full"
        bg="blue.400"
        filter="blur(10px)"
        opacity={0.4}
        // animate={{
        //   scale: [1, 1.1, 1],
        //   rotate: [0, 10, 0],
        // }}
        // transition={{
        //   duration: 10,
        //   repeat: Infinity,
        //   repeatType: "reverse",
        // }}
      />
      <MotionBox
        position="absolute"
        bottom="-15%"
        right="-10%"
        w="40%"
        h="40%"
        borderRadius="full"
        bg="purple.500"
        filter="blur(10px)"
        opacity={0.4}
        // animate={{
        //   scale: [1, 1.2, 1],
        //   rotate: [0, -15, 0],
        // }}
        // transition={{
        //   duration: 12,
        //   repeat: Infinity,
        //   repeatType: "reverse",
        // }}
      />

      {/* Hero Section */}
      <Container maxW="container.xl" centerContent>
        <VStack
          spacing={8}
          alignItems="center"
          justifyContent="center"
          textAlign="center"
          h="100vh"
        >
          <MotionBox
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            <Heading as="h1" size="3xl" color={textColor} mb={4}>
              Automate Your Trading Like Wall Street
            </Heading>
            <Text fontSize="xl" color={textColor} mb={8}>
              Nova Algo puts your portfolio on autopilot with professional-grade
              algorithms
            </Text>
            <HStack
              mx="auto"
              gap={4}
              display={"inline-flex"}
              wrap={"wrap"}
              // align={"center"}
              justify={"center"}
            >
              <Link
                href="/sign-up"
                size={"lg"}
                as={MotionButton}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                colorScheme="blue"
                pl={8}
                pr={3}
                gap={2}
              >
                Automate My Trading{" "}
                <Box
                  as={motion.div}
                  whileHover={{ translateX: 10 }}
                  rounded={"full"}
                  bg={"white"}
                  color={"blue.500"}
                  p={2}
                >
                  <LuArrowRight />
                </Box>
              </Link>
              <Button size={"lg"} colorScheme="blue" variant="outline" px={8}>
                See How it works
              </Button>
            </HStack>
          </MotionBox>
        </VStack>
      </Container>
    </Box>
  );
};

export default Hero;
