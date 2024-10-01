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
  AbsoluteCenter,
  Divider,
  useDisclosure,
} from "@chakra-ui/react";
import { motion } from "framer-motion";
import { FaGoogle } from "react-icons/fa";
import { LuArrowRight } from "react-icons/lu";
import { ResponsiveModalSheet } from "../SheetOrModal";
import { useGoogleLogin } from "@/hooks";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const MotionBox = motion.create(Box as any);
// eslint-disable-next-line @typescript-eslint/no-explicit-any
// const MotionButton = motion.create(Button as any);
const Hero = () => {
  const textColor = useColorModeValue("gray.800", "gray.100");
  const { handleLogin } = useGoogleLogin();
  const { isOpen, onOpen, onClose } = useDisclosure();
  return (
    <>
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
                Nova Algo puts your portfolio on autopilot with
                professional-grade algorithms
              </Text>
              <HStack
                mx="auto"
                gap={4}
                display={"inline-flex"}
                wrap={"wrap"}
                // align={"center"}
                justify={"center"}
              >
                {/* <Link href="/sign-up"> */}
                <Button
                  as={motion.button}
                  size={"lg"}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={onOpen}
                  pl={8}
                  pr={3}
                  gap={2}
                  bgGradient="linear(to-r, #4A90E2, #9B59B6)"
                  color="white"
                  _hover={{
                    bgGradient: "linear(to-r, #4A90E2, #9B59B6)",
                  }}
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
                {/* </Link> */}
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
      <ResponsiveModalSheet
        title=""
        isOpen={isOpen}
        onClose={onClose}
        content={
          <>
            <VStack>
              <w3m-button />

              <Box position="relative" padding="4">
                <Divider />
                <AbsoluteCenter bg="white" px="4">
                  or
                </AbsoluteCenter>
              </Box>
              <Button
                variant={"outline"}
                leftIcon={<FaGoogle />}
                onClick={() => handleLogin()}
              >
                Continue with Google
              </Button>
            </VStack>
          </>
        }
      />
    </>
  );
};

export default Hero;
