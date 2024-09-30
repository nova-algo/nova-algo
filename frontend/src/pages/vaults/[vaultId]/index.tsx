/* eslint-disable @typescript-eslint/no-explicit-any */
import React from "react";
import {
  Box,
  Flex,
  HStack,
  Heading,
  Stack,
  Tab,
  TabList,
  TabPanel,
  TabPanels,
  Tabs,
  Text,
  useColorModeValue,
} from "@chakra-ui/react";
import { motion } from "framer-motion";

import { GetServerSidePropsContext, InferGetServerSidePropsType } from "next";

import DataList from "@/components/DataList";
import { DepositOrWithdrawalBox } from "@/components/DepositOrWithdrawalBox";
import { LineDivider } from "@/components/LineDivider";
import MarkdownRenderer from "@/components/MarkdownRenderer";
import SectionHeading from "@/components/SectionHeading";
import VaultChart from "@/components/VaultChart";

import { vaults } from "@/lib/vaults";
import Header from "@/components/Header";

const MotionBox = motion.create(Box as any);
const MotionFlex = motion.create(Flex as any);

export default function VaultPage({
  vault,
}: InferGetServerSidePropsType<typeof getServerSideProps>) {
  // const bgColor = useColorModeValue("white", "gray.800");
  const textColor = useColorModeValue("gray.800", "white");
  const borderColor = useColorModeValue("gray.200", "gray.600");

  const tabBtnStyle = {
    fontSize: { xl: "24px", base: "16px", md: "20px" },
    border: { sm: "2px" },
    borderColor: { sm: "transparent" },
    _hover: {
      bg: "blue.100",
      color: "blue.600",
      borderColor: "blue.200",
    },
    rounded: { sm: "full", base: "md" },
    color: "gray.600",
    fontWeight: 400,
    _selected: {
      color: "white",
      bg: "blue.500",
      borderColor: "transparent",
      _hover: {
        borderColor: "transparent",
        bg: "blue.600",
        color: "white",
      },
    },
    w: { base: "full", sm: "auto" },
    flexShrink: { base: 0, sm: 1 },
    px: { lg: 6, base: 3, md: 4 },
  };

  const vaultPerformanceData = {
    "Total Earnings (All Time)": "$2,903,690.85",
    "Cumulative Return": "40.65%",
    APY: "0.95%",
    "Max Daily Drawdown": "-0.87%",
    "30D Volume": "$250,698,411.18",
  };

  const yourPerformanceData = {
    "Total Earnings (All Time)": "$0.00",
    "Your Cumulative Net Deposits": "$1.15",
    "Your Balance": "$1.14",
    ROI: "0.0000%",
    "Vault Share": "0%",
    "Max Daily Drawdown": "0.00%",
  };

  return (
    <MotionBox
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      <Header />
      <MotionBox
        as="main"
        mx="auto"
        maxW="1350px"
        initial={{ y: 20 }}
        animate={{ y: 0 }}
        transition={{ duration: 0.5, delay: 0.2 }}
      >
        <MotionBox
          textAlign="center"
          py={{ lg: 12, base: 10 }}
          px={4}
          mt={10}
          bg={`#000b url(
            "/images/vault-hero-bg.png"
          ) center / cover no-repeat`}
          //   backgroundBlendMode="darken"
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5, delay: 0.4 }}
        >
          <Heading size={{ sm: "3xl", base: "2xl" }} mb={4} color="white">
            {vault?.name}
          </Heading>
          <Text
            fontSize={{ sm: "22px", base: "20px" }}
            color="gray.300"
            maxW={1000}
            mx="auto"
          >
            {vault?.description}
          </Text>
        </MotionBox>

        <HStack
          wrap={{ base: "wrap", sm: "nowrap" }}
          gap={{ lg: 10, base: 5, md: 8 }}
          justify="center"
          px={4}
          py={10}
        >
          <Stack align="center">
            <Text
              fontWeight={600}
              fontSize={{ md: "35px", sm: "30px", base: "28px" }}
              color={textColor}
            >
              $25,865,348.01
            </Text>
            <Text color="gray.500" fontSize="17px">
              Total Value Locked
            </Text>
          </Stack>

          <LineDivider
            styleProps={{
              w: { base: "100%", sm: "2px", md: "3px" },
              h: { base: "2px", sm: "55px" },
              flexShrink: 0,
            }}
          />

          <Stack align="center">
            <Text
              fontWeight={600}
              fontSize={{ md: "35px", sm: "30px", base: "28px" }}
              color={textColor}
            >
              $30,000,000.00
            </Text>
            <Text color="gray.500" fontSize="17px">
              Max Capacity
            </Text>
          </Stack>
        </HStack>

        <MotionFlex
          mx="auto"
          wrap={{ lg: "nowrap", base: "wrap" }}
          justify="space-between"
          maxW="1350px"
          pb={10}
          px={{ lg: 6, md: 5, base: 2 }}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.6 }}
        >
          <Tabs
            display="flex"
            flexDir="column"
            mx="auto"
            colorScheme="blue"
            variant="solid-rounded"
            px={{ base: 2, lg: 3 }}
            w={{ lg: "fit-content", base: "100%" }}
          >
            <TabList
              // maxW="fit-content"
              flexWrap={{ base: "wrap", sm: "nowrap" }}
              justifyContent={{ base: "center" }}
              gap={{ lg: 8, base: 4, sm: 6 }}
              border="1px"
              rounded={{ sm: "full", base: "md" }}
              borderColor={borderColor}
              pos="relative"
              mx="auto"
              mb={8}
            >
              <Tab {...tabBtnStyle}>Vault Performance</Tab>
              <Tab {...tabBtnStyle}>Your Performance</Tab>
              <Tab {...tabBtnStyle}>Overview</Tab>
            </TabList>

            <TabPanels>
              <TabPanel px={{ base: 0, md: 4 }}>
                <Stack gap={5} flex={1}>
                  <SectionHeading
                    title="Performance Breakdown"
                    // containerStyleProps={{ mt: 0 }}
                  />
                  <DataList data={vaultPerformanceData} />
                  <Box>
                    <SectionHeading title="Cumulative Performance" />
                    <VaultChart />
                  </Box>
                  <SectionHeading title="Vault Details" />
                </Stack>
              </TabPanel>

              <TabPanel>
                <Stack gap={5}>
                  <Box>
                    <SectionHeading
                      title="Summary"
                      //   containerStyleProps={{ mt: 0 }}
                    />
                    <HStack
                      my={6}
                      divider={<LineDivider styleProps={{ w: "2px" }} />}
                      justify="space-around"
                    >
                      <Stack fontSize="18px" textAlign="center">
                        <Text
                          fontSize={{ base: "20px", md: "22px" }}
                          fontWeight={700}
                          color={textColor}
                        >
                          $0.0
                        </Text>
                        <Text color="gray.500">Your Balance</Text>
                      </Stack>
                      <Stack fontSize="18px" textAlign="center">
                        <Text
                          fontSize={{ base: "20px", md: "22px" }}
                          fontWeight={700}
                          color={textColor}
                        >
                          $0.00
                        </Text>
                        <Text color="gray.500">Total Earnings (All Time)</Text>
                      </Stack>
                    </HStack>
                  </Box>
                  <Box>
                    <SectionHeading title="Performance Breakdown" />
                    <DataList data={yourPerformanceData} />
                  </Box>
                </Stack>
              </TabPanel>

              <TabPanel>
                <Stack gap={6}>
                  <Box>
                    <SectionHeading
                      title="Strategy"
                      //   containerStyleProps={{ mt: 0 }}
                    />
                    <MarkdownRenderer markdown={vault?.strategy as string} />
                  </Box>
                  <Box>
                    <SectionHeading title="Risks" />
                    <MarkdownRenderer markdown={vault?.risk as string} />
                  </Box>
                </Stack>
              </TabPanel>
            </TabPanels>
          </Tabs>

          <Box
            mx={"auto"}
            px={0}
            minW={{ md: 400, base: 250 }}
            w={{ base: "full", lg: "auto" }}
            maxW={{ base: "600", lg: 400 }}
          >
            <DepositOrWithdrawalBox
              // walletToken={walletToken}
              // walletBalance={walletBalance}
              width="full"
              maxW="auto"
            />
          </Box>
        </MotionFlex>
      </MotionBox>
    </MotionBox>
  );
}

export async function getServerSideProps(ctx: GetServerSidePropsContext) {
  const { vaultId } = ctx.query;
  const vault = vaults.find((v) => v.id === (vaultId as string));
  return { props: { vault } };
}
