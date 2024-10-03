import React from "react";
import {
  Box,
  Flex,
  Skeleton,
  SkeletonText,
  HStack,
  VStack,
} from "@chakra-ui/react";

const VaultLoadingSkeleton = () => {
  return (
    <Box maxW="1350px" mx="auto" px={4}>
      {/* Header Skeleton */}
      <Skeleton height="60px" mb={10} rounded={"2xl"} />

      {/* Hero Section Skeleton */}
      <Skeleton height="200px" mb={10} rounded={"2xl"} />

      {/* Stats Section Skeleton */}
      <HStack justify="center" mb={10}>
        <SkeletonText
          noOfLines={2}
          spacing={4}
          skeletonHeight={4}
          width="150px"
          rounded={"2xl"}
        />
        <Skeleton height="50px" width="2px" rounded={"2xl"} />
        <SkeletonText
          rounded={"2xl"}
          noOfLines={2}
          spacing={4}
          skeletonHeight={4}
          width="150px"
        />
      </HStack>

      {/* Main Content Skeleton */}
      <Flex direction={{ base: "column", lg: "row" }} gap={10}>
        <VStack align="stretch" flex={1} spacing={8}>
          {/* Tabs Skeleton */}
          <Skeleton height="40px" width="100%" rounded={"2xl"} />

          {/* Performance Breakdown Skeleton */}
          <VStack align="stretch" spacing={4}>
            <Skeleton height="24px" width="200px" rounded={"2xl"} />
            <SkeletonText
              noOfLines={5}
              rounded={"2xl"}
              spacing={4}
              skeletonHeight={4}
            />
          </VStack>

          {/* Chart Skeleton */}
          <VStack align="stretch" spacing={4}>
            <Skeleton height="24px" width="200px" rounded={"2xl"} />
            <Skeleton height="300px" rounded={"2xl"} />
          </VStack>

          {/* Vault Details Skeleton */}
          <VStack align="stretch" spacing={4}>
            <Skeleton height="24px" width="200px" rounded={"2xl"} />
            <SkeletonText
              noOfLines={8}
              spacing={4}
              rounded={"2xl"}
              skeletonHeight={4}
            />
          </VStack>
        </VStack>

        {/* Deposit/Withdrawal Box Skeleton */}
        <Box minW={{ md: 400, base: 250 }} maxW={{ base: "600", lg: 400 }}>
          <Skeleton height="400px" rounded={"2xl"} />
        </Box>
      </Flex>
    </Box>
  );
};

export default VaultLoadingSkeleton;
