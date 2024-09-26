import {
  Box,
  Heading,
  Text,
  Container,
  useColorModeValue,
  SimpleGrid,
  Icon,
  Flex,
  Avatar,
} from "@chakra-ui/react";
import { motion } from "framer-motion";
import { LuQuote } from "react-icons/lu";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const MotionBox = motion.create(Box as any);
interface TestimonialCardProps {
  content: string;
  author: string;
  position: string;
}

const TestimonialCard: React.FC<TestimonialCardProps> = ({
  content,
  author,
  position,
}) => {
  const bgColor = useColorModeValue("white", "gray.800");
  const borderColor = useColorModeValue("gray.200", "gray.700");

  return (
    <MotionBox
      borderWidth={1}
      borderRadius="3xl"
      borderColor={borderColor}
      p={6}
      bg={bgColor}
      boxShadow="md"
      whileHover={{ y: -5, boxShadow: "xl" }}
      transition={{ duration: 0.3 }}
    >
      <Icon as={LuQuote} w={8} h={8} color="blue.500" mb={4} />
      <Text fontSize="md" fontStyle="italic" mb={4}>
        {content}
      </Text>
      <Flex align="center">
        <Avatar size="sm" mr={2} />
        <Box>
          <Text fontWeight="bold">{author}</Text>
          <Text fontSize="sm" color="gray.500">
            {position}
          </Text>
        </Box>
      </Flex>
    </MotionBox>
  );
};
export default function Testimonials() {
  return (
    <Container maxW="container.xl" py={20}>
      <Heading as="h2" size="2xl" mb={12} textAlign="center">
        What Our Users Say
      </Heading>
      <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={10}>
        <TestimonialCard
          content="Nova Algo's AI-powered vaults have completely transformed my trading strategy. The results speak for themselves!"
          author="Alex Chen"
          position="Crypto Enthusiast"
        />
        <TestimonialCard
          content="I've tried many trading bots, but Nova Algo's automated vaults are in a league of their own. The AI adaptation is impressive."
          author="Sarah Johnson"
          position="Day Trader"
        />
        <TestimonialCard
          content="As a busy professional, Nova Algo gives me peace of mind. My portfolio is optimized 24/7 without any effort on my part."
          author="Michael Lee"
          position="Tech Executive"
        />
      </SimpleGrid>
    </Container>
  );
}
