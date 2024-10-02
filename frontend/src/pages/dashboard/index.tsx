import React, { createElement } from "react";
import { Box, Grid, Heading, Text, VStack, HStack } from "@chakra-ui/react";
import { LuWallet, LuTrendingUp, LuPieChart } from "react-icons/lu";
import { IconType } from "react-icons";
import VaultChart from "@/components/VaultChart";
import { useAppContext } from "@/context/app-context";
import { Link } from "@chakra-ui/next-js";

const UserDashboard = () => {
  const { balance, balanceSymbol } = useAppContext();
  return (
    <>
      <HStack bg={"gray.100"} height={"50px"} p={4}>
        <Link href={"/"}>Back to site</Link>
      </HStack>
      <Box p={{ base: 4, md: 6, lg: 8 }}>
        <HStack wrap={"wrap"} justify={"space-between"}>
          <Heading mb={6}>Welcome, User</Heading>
          <Box>
            <Text color={"gray.600"}>Wallet balance:</Text>
            <Text as={"span"}>{balanceSymbol}:</Text>{" "}
            <Text fontWeight={600} as={"span"}>
              {(+balance).toFixed(4)}
            </Text>
          </Box>
        </HStack>
        <Grid
          templateColumns={{
            base: "repeat(autofit,minmax(250px,1fr))",
            md: "repeat(3, 1fr)",
          }}
          gap={6}
          mb={8}
        >
          <StatCard icon={LuWallet} title="Total Balance" value="$10,245.67" />
          <StatCard
            icon={LuTrendingUp}
            title="Total Profit"
            value="$1,234.56"
          />
          <StatCard icon={LuPieChart} title="Active Vaults" value="3" />
        </Grid>
        <Box mb={8}>
          <Heading size="md" mb={4}>
            Performance Overview
          </Heading>
          <VaultChart />
        </Box>
        <Grid
          templateColumns={{
            base: "repeat(autofit,minmax(250px,1fr))",
            md: "repeat(2, 1fr)",
          }}
          gap={6}
        >
          <Box p={6} borderWidth={1} borderRadius="lg">
            <Heading size="md" mb={4}>
              Your Vaults
            </Heading>
            <VStack align="stretch" spacing={4}>
              <VaultItem name="Growth Fund" balance="$5,000" profit="+12.3%" />
              <VaultItem
                name="Tech Innovators"
                balance="$3,000"
                profit="+8.7%"
              />
              <VaultItem name="Green Energy" balance="$2,245" profit="+5.2%" />
            </VStack>
          </Box>
          <Box p={6} borderWidth={1} borderRadius="lg">
            <Heading size="md" mb={4}>
              Recent Transactions
            </Heading>
            <VStack align="stretch" spacing={4}>
              <TransactionItem
                type="Deposit"
                amount="$1,000"
                date="2023-06-01"
              />
              <TransactionItem
                type="Withdrawal"
                amount="$500"
                date="2023-05-28"
              />
              <TransactionItem
                type="Deposit"
                amount="$2,000"
                date="2023-05-15"
              />
            </VStack>
          </Box>
        </Grid>
      </Box>
    </>
  );
};

const StatCard = ({
  icon,
  title,
  value,
}: {
  icon: IconType;
  title: string;
  value: string;
}) => (
  <HStack p={6} borderWidth={1} borderRadius="lg" spacing={4}>
    {createElement(icon)}
    <VStack align="start" spacing={1}>
      <Text fontSize="sm" color="gray.500">
        {title}
      </Text>
      <Text fontSize="2xl" fontWeight="bold">
        {value}
      </Text>
    </VStack>
  </HStack>
);

const VaultItem = ({
  name,
  balance,
  profit,
}: {
  name: string;
  balance: string;
  profit: string;
}) => (
  <HStack justify="space-between">
    <VStack align="start" spacing={0}>
      <Text fontWeight="bold">{name}</Text>
      <Text fontSize="sm" color="gray.500">
        {balance}
      </Text>
    </VStack>
    <Text color="green.500" fontWeight="bold">
      {profit}
    </Text>
  </HStack>
);

const TransactionItem = ({
  type,
  amount,
  date,
}: {
  type: string;
  date: string;
  amount: string;
}) => (
  <HStack justify="space-between">
    <VStack align="start" spacing={0}>
      <Text fontWeight="bold">{type}</Text>
      <Text fontSize="sm" color="gray.500">
        {date}
      </Text>
    </VStack>
    <Text>{amount}</Text>
  </HStack>
);

export default UserDashboard;
