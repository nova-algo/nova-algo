import {
  Box,
  Heading,
  Text,
  Container,
  useColorModeValue,
  SimpleGrid,
  Icon,
  Flex,
} from "@chakra-ui/react";
import { motion } from "framer-motion";
import { IconType } from "react-icons";
import { FaRobot, FaChartLine, FaShieldAlt, FaClock } from "react-icons/fa";
import Benefits from "./Benefits";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const MotionBox = motion.create(Box as any);
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const MotionFlex = motion.create(Flex as any);

interface FeatureCardProps {
  icon: IconType;
  title: string;
  description: string;
}

const FeatureCard: React.FC<FeatureCardProps> = ({
  icon,
  title,
  description,
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
      <Icon as={icon} w={10} h={10} color="blue.500" mb={4} />
      <Heading as="h3" size="md" mb={2}>
        {title}
      </Heading>
      <Text>{description}</Text>
    </MotionBox>
  );
};

const Featured = () => {
  return (
    <>
      <Container maxW="container.xl" py={20}>
        <MotionFlex
          direction="column"
          alignItems="center"
          initial={{ opacity: 0, y: 50 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2 }}
        >
          <Heading as="h2" size="2xl" mb={4} textAlign="center">
            Why Choose Nova Algo?
          </Heading>
          <Text fontSize="xl" textAlign="center" mb={12} maxW="2xl">
            Experience the power of Advanced automated vaults, designed to
            optimize your trading portfolio.
          </Text>
        </MotionFlex>
        <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={10}>
          <FeatureCard
            icon={FaRobot}
            title="Advanced automated Vaults"
            description="Our advanced automated vaults manages your portfolio, executing trades with precision and adaptability."
          />
          <FeatureCard
            icon={FaChartLine}
            title="Real-Time Analytics"
            description="Stay informed with up-to-the-minute performance metrics and insights on your automated vault."
          />
          <FeatureCard
            icon={FaShieldAlt}
            title="Bank-Grade Security"
            description="Your investments are protected by state-of-the-art security measures within our vaults."
          />
          <FeatureCard
            icon={FaClock}
            title="24/7 Automation"
            description="Our automated vaults optimizes your portfolio around the clock, even while you sleep."
          />
        </SimpleGrid>
      </Container>

      {/* Benefits Section */}
      <Benefits />
    </>
  );
};

export default Featured;
