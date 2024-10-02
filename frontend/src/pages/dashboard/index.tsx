import React, { createElement, ReactNode } from "react";
import {
  Box,
  Grid,
  Heading,
  Text,
  VStack,
  HStack,
  Flex,
  Button,
  Drawer,
  DrawerBody,
  DrawerHeader,
  DrawerOverlay,
  DrawerContent,
  DrawerCloseButton,
  useDisclosure,
  useBreakpointValue,
  Image,
} from "@chakra-ui/react";
import {
  LuWallet,
  LuTrendingUp,
  LuPieChart,
  LuHome,
  LuUser,
  LuSettings,
  LuMenu,
  LuPlus,
} from "react-icons/lu";
import { IconType } from "react-icons";
import VaultChart from "@/components/VaultChart";
import { useAppContext, useNextAuthSession } from "@/context/app-context";
import { Link } from "@chakra-ui/next-js";

const UserDashboard = () => {
  const { balance, balanceSymbol, accountType } = useAppContext();
  const { data: session } = useNextAuthSession();
  const { isOpen, onOpen, onClose } = useDisclosure();
  const isMobile = useBreakpointValue({ base: true, md: false });
  async function handleMercuryo() {
    window.open(
      "https://sandbox-exchange.mrcr.io?address=0xA14691F9f1F851bd0c20115Ec10B25FC174371DF&widget_id=498a52be-6c66-415d-b9a6-44987d8dc031?signature=c20283cedb882fbfd27fc7ee0cfe6db930b732f669a3abee698967e3984ae7dfd24e058d7cecf37da0bb2fb133a24e47b4b3fc34578788ca07857f6ed1129284",
      "_blank"
    );
  }
  return (
    <Flex>
      {!isMobile && (
        <Box
          width="250px"
          bg="gray.100"
          p={4}
          height="100vh"
          pos={"sticky"}
          top={0}
        >
          <Image
            src="/images/desktop-logo-white.png"
            alt="app logo"
            maxW={"100px"}
            ml={3}
            mixBlendMode={"difference"}
            mb={5}
          />
          <Sidebar />
        </Box>
      )}
      <Box flex={1}>
        <HStack
          bg="gray.100"
          height="50px"
          p={4}
          justify="space-between"
          pos={"sticky"}
          top={0}
          zIndex={10}
        >
          {isMobile && (
            <Button onClick={onOpen} leftIcon={<LuMenu />} variant="ghost">
              Menu
            </Button>
          )}
          <Link href="/">Back to site</Link>
        </HStack>
        <Box p={{ base: 4, md: 6, lg: 8 }}>
          <HStack wrap="wrap" justify="space-between" mb={6}>
            <Heading>
              Welcome,{" "}
              {accountType === "GOOGLE"
                ? session?.user?.name?.split(" ")[0]
                : "User"}
            </Heading>
            <Box>
              <Text color="gray.600">Wallet balance:</Text>
              <Text as="span">{balanceSymbol}:</Text>{" "}
              <Text fontWeight={600} as="span">
                {(+balance).toFixed(4)}
              </Text>
            </Box>
          </HStack>
          <Grid
            templateColumns={{
              base: "repeat(autofit,minmax(250px,1fr))",
              lg: "repeat(3, 1fr)",
            }}
            gap={6}
            mb={8}
          >
            <StatCard icon={LuWallet} title="Total Balance" value="$10,245.67">
              <HStack mt={4}>
                <Button
                  onClick={handleMercuryo}
                  size={"sm"}
                  leftIcon={<LuPlus />}
                >
                  Fund wallet
                </Button>
              </HStack>
            </StatCard>
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
              lg: "repeat(2, 1fr)",
            }}
            gap={6}
          >
            <Box p={6} borderWidth={1} borderRadius="lg">
              <Heading size="md" mb={4}>
                Your Vaults
              </Heading>
              <VStack align="stretch" spacing={4}>
                <VaultItem
                  name="Growth Fund"
                  balance="$5,000"
                  profit="+12.3%"
                />
                <VaultItem
                  name="Tech Innovators"
                  balance="$3,000"
                  profit="+8.7%"
                />
                <VaultItem
                  name="Green Energy"
                  balance="$2,245"
                  profit="+5.2%"
                />
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
      </Box>
      <Drawer isOpen={isOpen} placement="left" onClose={onClose}>
        <DrawerOverlay />
        <DrawerContent>
          <DrawerCloseButton />
          <DrawerHeader>Menu</DrawerHeader>
          <DrawerBody>
            <Sidebar />
          </DrawerBody>
        </DrawerContent>
      </Drawer>
    </Flex>
  );
};

const Sidebar = () => (
  <VStack spacing={4} align="stretch">
    <SidebarItem icon={LuHome} label="Dashboard" />
    <SidebarItem icon={LuWallet} label="Vaults" />
    <SidebarItem icon={LuTrendingUp} label="Analytics" />
    <SidebarItem icon={LuUser} label="Profile" />
    <SidebarItem icon={LuSettings} label="Settings" />
  </VStack>
);

const SidebarItem = ({ icon, label }: { icon: IconType; label: string }) => (
  <Button
    leftIcon={createElement(icon)}
    justifyContent="flex-start"
    variant="ghost"
    width="100%"
  >
    {label}
  </Button>
);

const StatCard = ({
  icon,
  title,
  value,
  children,
}: {
  icon: IconType;
  title: string;
  value: string;
  children?: ReactNode;
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
      {children}
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
