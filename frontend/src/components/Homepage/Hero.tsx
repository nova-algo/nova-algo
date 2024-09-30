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
  Image,
} from "@chakra-ui/react";
import { motion } from "framer-motion";
import { LuArrowRight } from "react-icons/lu";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const MotionBox = motion.create(Box as any);
// eslint-disable-next-line @typescript-eslint/no-explicit-any
// const MotionButton = motion.create(Button as any);
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
      >
        <svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
          <path
            fill="#0099ff"
            d="M42.1,-68.5C51.3,-59.7,53.1,-42.4,55,-28.1C56.9,-13.8,59,-2.5,61.3,11.6C63.6,25.7,66.1,42.6,60.6,57.1C55.2,71.6,41.6,83.7,27.5,82.8C13.4,81.9,-1.2,68,-17.4,62C-33.6,56,-51.2,57.8,-64.3,51.1C-77.3,44.3,-85.8,28.9,-87,13.2C-88.2,-2.5,-82.1,-18.6,-71.4,-28.7C-60.7,-38.7,-45.3,-42.7,-32.6,-49.8C-20,-57,-10,-67.4,3.3,-72.5C16.5,-77.5,33,-77.3,42.1,-68.5Z"
            transform="translate(100 100)"
          />
        </svg>
      </MotionBox>

      <Container maxW="container.xl" centerContent pos={"relative"}>
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
              <Link href="/sign-up">
                <Button
                  as={motion.button}
                  size={"lg"}
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
                </Button>
              </Link>
              <Button size={"lg"} colorScheme="blue" variant="outline" px={8}>
                See How it works
              </Button>
            </HStack>
          </MotionBox>
        </VStack>
      </Container>
      <Box mt={{ md: 10 }} pos={"relative"}>
        <Image
          display={"inline-block"}
          src="/images/wave.svg"
          alt="Hero Image"
          pos={"absolute"}
          bottom={0}
          left={0}
          right={0}
          w={"100vw"}
        />
      </Box>
    </Box>
  );
};

export default Hero;
