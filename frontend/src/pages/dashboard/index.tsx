import React, {
  createElement,
  MouseEvent,
  ReactNode,
  useEffect,
  useState,
} from "react";
import {
  Box,
  Grid,
  Heading,
  Text,
  VStack,
  HStack,
  Button,
  useDisclosure,
  ModalHeader,
  ModalContent,
  ModalOverlay,
  Modal,
  ModalBody,
  ModalCloseButton,
  FormControl,
  FormLabel,
  Stack,
  FormErrorMessage,
  NumberInput,
  NumberInputField,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  Spinner,
} from "@chakra-ui/react";
import {
  LuWallet,
  LuTrendingUp,
  LuPieChart,
  LuPlus,
  LuChevronDown,
  LuDollarSign,
  LuCoins,
} from "react-icons/lu";
import { IconType } from "react-icons";
import VaultChart from "@/components/VaultChart";
import { useAppContext, useNextAuthSession } from "@/context/app-context";
import { objectToQueryParams } from "@/utils";
import { useFormik } from "formik";
import { object, string } from "yup";
import { useRouter } from "next/router";
import { OktoContextType, useOkto } from "okto-sdk-react";
import Head from "next/head";
import DashboardWrapper from "@/components/DashboardWrapper";

type FormFields = {
  address: string;
  widget_id?: string;
  fiat_currency: string;
  fiat_amount: number;
  network: string;
  currency: string;
};
const UserDashboard = () => {
  const {
    balance,

    accountType,
    address,
    isAuthenticated,
    balanceInUSD,
    balanceSymbol,
  } = useAppContext();
  const [canLoad, setCanLoad] = useState(false);
  const { data: session } = useNextAuthSession();
  const { showWidgetModal } = useOkto() as OktoContextType;
  const router = useRouter();
  const {
    isOpen: isModalOpen,
    onOpen: onModalOpen,
    onClose: onModalClose,
  } = useDisclosure();
  const formik = useFormik({
    validationSchema: object({
      fiat_amount: string().required("Amount is required"),
    }),
    initialValues: {
      address,
      widget_id: process.env.NEXT_PUBLIC_MERCURYO_WIDGET_ID,
      fiat_currency: "USD",
      fiat_amount: 100,
      network: "SOLANA",
      currency: "SOL",
    },
    onSubmit: async (values) => {
      await handleMercuryo(values);
    },
  });

  async function fetchSignature(address: string) {
    const response = await fetch(
      "/api/mercuryo/signature?" + objectToQueryParams({ address })
    );
    const result = await response.json();
    const signature = result.data;
    return signature;
  }
  async function handleMercuryo(
    values: FormFields,
    type: "deposit" | "withdraw" = "deposit"
  ) {
    try {
      const signature = await fetchSignature(values.address);

      if (type === "withdraw") {
        window.open(
          "https://exchange.mercuryo.io/?" +
            objectToQueryParams({
              currency: "SOL",
              address,
              fiat_currency: "USD",
              amount: balance,
              type: "sell",
              signature,
            }),
          "popup"
        );
        return;
      }

      window.open(
        "https://exchange.mercuryo.io/?" +
          objectToQueryParams({ ...values, signature, type: "buy" }),
        "popup"
      );
      onModalClose();
    } catch (error) {
      console.log({ error }, "Error generating signature");
    }
  }
  async function handleWithdraw() {
    handleMercuryo(formik.values, "withdraw");
  }
  useEffect(() => {
    formik.setFieldValue("address", address);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [address]);
  function handleTokenSelect(e: MouseEvent<HTMLDivElement>) {
    const target = e.target as HTMLButtonElement;
    formik.setFieldValue("currency", target.value);
  }
  function handleCurrencySelect(e: MouseEvent<HTMLDivElement>) {
    const target = e.target as HTMLButtonElement;
    formik.setFieldValue("fiat_currency", target.value);
  }
  useEffect(() => {
    if (!isAuthenticated) {
      router.replace("/");
    } else {
      setCanLoad(true);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  if (!canLoad)
    return (
      <>
        <Spinner />
      </>
    );
  return (
    <>
      <Head>
        <title>Dashboard | NovaAlgo</title>
        <meta
          name="description"
          content="NovaAlgo is a decentralized cryptocurrency exchange platform."
        />
      </Head>
      <DashboardWrapper>
        <Box flex={1}>
          <Box p={{ base: 4, md: 6, lg: 8 }}>
            <HStack wrap="wrap" justify="space-between" mb={6}>
              <Heading>
                {accountType === "GOOGLE"
                  ? "Welcome, " + session?.user?.name?.split(" ")[0]
                  : "Welcome back"}
              </Heading>
            </HStack>
            <Grid
              templateColumns={{
                base: "repeat(autofit,minmax(250px,1fr))",
                lg: "repeat(3, 1fr)",
              }}
              gap={6}
              mb={8}
            >
              <StatCard
                icon={LuWallet}
                title="Total Balance"
                value={
                  <>
                    <HStack>
                      <Text>${balanceInUSD}</Text>
                      <Text fontSize={"smaller"}>
                        ({balanceSymbol}:{balance.substring(0, 6)})
                      </Text>
                    </HStack>
                  </>
                }
              >
                <HStack mt={3} wrap={{ base: "wrap", lg: "nowrap" }}>
                  <Button
                    onClick={() => {
                      accountType === "GOOGLE"
                        ? showWidgetModal()
                        : onModalOpen();
                    }}
                    size={"sm"}
                    leftIcon={<LuPlus />}
                  >
                    Fund wallet
                  </Button>
                </HStack>
              </StatCard>
              <StatCard icon={LuTrendingUp} title="Total Profit" value="$34.56">
                <HStack mt={3} wrap={"wrap"} spacing={"3"}>
                  <Button
                    // onClick={handleWithdraw}
                    size={"sm"}
                    leftIcon={<LuCoins />}
                  >
                    Withdraw crypto
                  </Button>
                  <Button
                    onClick={handleWithdraw}
                    size={"sm"}
                    leftIcon={<LuDollarSign />}
                  >
                    Withdraw Fiat
                  </Button>
                </HStack>
              </StatCard>
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
                    name="Drifting Tiger"
                    balance="$5,000"
                    profit="+12.3%"
                  />
                  <VaultItem
                    name="Bonking Dragon"
                    balance="$3,000"
                    profit="+8.7%"
                  />
                  <VaultItem
                    name="Gamma Vault"
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
                    date="2024-10-01"
                  />
                  <TransactionItem
                    type="Withdrawal"
                    amount="$500"
                    date="2024-09-28"
                  />
                  <TransactionItem
                    type="Deposit"
                    amount="$2,000"
                    date="2024-09-15"
                  />
                </VStack>
              </Box>
            </Grid>
          </Box>
        </Box>

        <Modal
          isOpen={isModalOpen}
          onClose={onModalClose}
          size={{ base: "full", sm: "md" }}
          motionPreset={"slideInBottom"}
        >
          <ModalOverlay />
          <ModalContent rounded={"24px"}>
            <ModalHeader>Fund Wallet</ModalHeader>
            <ModalCloseButton />
            <ModalBody>
              <Stack
                as={"form"}
                spacing={4}
                // @ts-expect-error works fine
                onSubmit={formik.handleSubmit}
              >
                <FormControl
                  isInvalid={
                    !!formik.errors.fiat_amount && formik.touched.fiat_amount
                  }
                >
                  <FormLabel htmlFor="fiat_amount">Amount:</FormLabel>
                  <NumberInput
                    isRequired
                    id="fiat_amount"
                    name="fiat_amount"
                    min={1}
                    value={formik.values.fiat_amount}
                  >
                    <NumberInputField
                      onChange={formik.handleChange}
                      rounded={"full"}
                      placeholder="Enter amount"
                    />
                    {formik.errors.fiat_amount && (
                      <FormErrorMessage>
                        {formik.errors.fiat_amount}
                      </FormErrorMessage>
                    )}
                  </NumberInput>
                </FormControl>
                <FormControl>
                  <FormLabel htmlFor="currency">Currency:</FormLabel>
                  <Menu>
                    <MenuButton
                      variant={"outline"}
                      id="currency"
                      as={Button}
                      rightIcon={<LuChevronDown />}
                    >
                      {formik.values.fiat_currency}
                    </MenuButton>
                    <MenuList onClick={handleCurrencySelect}>
                      <MenuItem value="USD">USD</MenuItem>
                      <MenuItem value="EUR">EUR</MenuItem>
                    </MenuList>
                  </Menu>
                </FormControl>
                <FormControl>
                  <FormLabel htmlFor="token">Token:</FormLabel>
                  <Menu>
                    <MenuButton
                      variant={"outline"}
                      id="token"
                      as={Button}
                      rightIcon={<LuChevronDown />}
                    >
                      {formik.values.currency}
                    </MenuButton>
                    <MenuList onClick={handleTokenSelect}>
                      <MenuItem value="USDT">USDT</MenuItem>
                      <MenuItem value="USDC">USDC</MenuItem>
                      <MenuItem value="SOL">SOL</MenuItem>
                    </MenuList>
                  </Menu>
                </FormControl>
                <Stack>
                  <Button
                    isLoading={formik.isSubmitting}
                    loadingText="Redirecting you..."
                    type="submit"
                    colorScheme="blue"
                  >
                    Fund Wallet
                  </Button>
                  <Text
                    color={"gray.500"}
                    fontSize={"x-small"}
                    textAlign={"center"}
                  >
                    You will be redirected to Mercuryo to complete the
                    transaction.
                  </Text>
                </Stack>
              </Stack>
            </ModalBody>
          </ModalContent>
        </Modal>
      </DashboardWrapper>
    </>
  );
};

const StatCard = ({
  icon,
  title,
  value,
  children,
}: {
  icon: IconType;
  title: string;
  value: string | ReactNode;
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
