import React from "react";
import { Box, Heading, useColorModeValue } from "@chakra-ui/react";
import { motion } from "framer-motion";

interface SectionHeadingProps {
  title: string;
  hideBorder?: boolean;
  containerProps?: React.ComponentProps<typeof Box>;
  headingProps?: React.ComponentProps<typeof Heading>;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const MotionBox = motion.create(Box as any);

const SectionHeading: React.FC<SectionHeadingProps> = ({
  title,
  hideBorder = false,
  containerProps,
  headingProps,
}) => {
  const borderColor = useColorModeValue("blue.500", "blue.300");
  const textColor = useColorModeValue("gray.800", "white");

  return (
    <MotionBox
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      position="relative"
      mb={6}
      {...containerProps}
    >
      <Heading
        as="h2"
        fontSize={{ base: "xl", md: "2xl" }}
        fontWeight="bold"
        color={textColor}
        {...headingProps}
      >
        {title}
      </Heading>
      {!hideBorder && (
        <Box
          position="absolute"
          bottom="-2px"
          left="0"
          width="50px"
          height="3px"
          borderRadius="full"
          bgGradient={`linear(to-r, ${borderColor}, ${borderColor})`}
        />
      )}
    </MotionBox>
  );
};

export default SectionHeading;
