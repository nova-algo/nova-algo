import {
  Box,
  Heading,
  Text,
  Container,
  useColorModeValue,
  SimpleGrid,
  Flex,
  Image,
} from "@chakra-ui/react";
import { motion } from "framer-motion";
import Benefits from "./Benefits";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const MotionBox = motion.create(Box as any);
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const MotionFlex = motion.create(Flex as any);

interface FeatureCardProps {
  icon: string;
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
      <Image alt="icon" src={icon} w={12} h={12} color="blue.500" mb={1} />
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
            icon={"/icons/vault-lock.svg"}
            title="Advanced automated Vaults"
            description="Our advanced automated vaults manages your portfolio, executing trades with precision and adaptability."
          />
          <FeatureCard
            icon={"/icons/Analytics.svg"}
            title="Real-Time Analytics"
            description="Stay informed with up-to-the-minute performance metrics and insights on your automated vault."
          />
          <FeatureCard
            icon={"/icons/security-shield.svg"}
            title="Bank-Grade Security"
            description="Your investments are protected by state-of-the-art security measures within our vaults."
          />
          <FeatureCard
            icon={"/icons/247-shield.svg"}
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
