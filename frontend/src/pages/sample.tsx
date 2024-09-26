import React from "react";
import {
  Box,
  VStack,
  Heading,
  Text,
  Button,
  Container,
  useColorModeValue,
  SimpleGrid,
  Icon,
  Flex,
  Avatar,
  Wrap,
  WrapItem,
} from "@chakra-ui/react";
import { motion, useScroll, useTransform, MotionProps } from "framer-motion";
import {
  FaRobot,
  FaChartLine,
  FaShieldAlt,
  FaClock,
  FaQuoteLeft,
} from "react-icons/fa";
import { IconType } from "react-icons";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const MotionBox = motion.create(Box);
const MotionFlex = motion.create(Flex);

const Homepage: React.FC = () => {
  const bgColor = useColorModeValue("gray.50", "gray.900");
  const textColor = useColorModeValue("gray.800", "gray.100");

  const { scrollY } = useScroll();
  const opacity = useTransform(scrollY, [0, 200], [0, 1]);

  return (
    <Box bg={bgColor} minH="100vh" position="relative" overflow="hidden">
      {/* Background blobs and Hero Section (remain the same) */}
      <MotionBox
        position="absolute"
        top="-10%"
        left="-5%"
        w="30%"
        h="30%"
        borderRadius="full"
        bg="blue.100"
        filter="blur(70px)"
        opacity={0.4}
        animate={{
          scale: [1, 1.1, 1],
          rotate: [0, 10, 0],
        }}
        transition={{
          duration: 10,
          repeat: Infinity,
          repeatType: "reverse",
        }}
      />
      <MotionBox
        position="absolute"
        bottom="-15%"
        right="-10%"
        w="40%"
        h="40%"
        borderRadius="full"
        bg="purple.100"
        filter="blur(70px)"
        opacity={0.4}
        animate={{
          scale: [1, 1.2, 1],
          rotate: [0, -15, 0],
        }}
        transition={{
          duration: 12,
          repeat: Infinity,
          repeatType: "reverse",
        }}
      />
      {/* Features Section */}

      {/* Benefits Section */}

      {/* Testimonial Section */}

      {/* Footer */}
    </Box>
  );
};

export default Homepage;
