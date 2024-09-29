/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useState } from "react";
import {
  Box,
  Button,
  FormControl,
  FormLabel,
  HStack,
  Input,
  Tab,
  TabList,
  TabPanel,
  TabPanels,
  Tabs,
  Text,
  useToast,
  VStack,
  useColorModeValue,
} from "@chakra-ui/react";
import { useFormik } from "formik";
import { motion } from "framer-motion";
import { CustomRadioGroup } from "./CustomRadioGroup";

const MotionBox = motion(Box as any);
const MotionButton = motion(Button as any);

const TradeTypeBox = ({
  walletBalance,
  walletToken,
  type,
}: {
  walletBalance: number;
  walletToken: string;
  type: "deposit" | "withdrawal";
}) => {
  const toast = useToast();
  const [amount, setAmount] = useState("");
  const bgColor = useColorModeValue("white", "gray.800");
  const borderColor = useColorModeValue("gray.200", "gray.600");
  const textColor = useColorModeValue("gray.800", "white");

  const formik = useFormik({
    initialValues: { amount: "" },
    onSubmit: () => {
      toast({
        title: `${
          type === "deposit" ? "Deposited" : "Withdrawal request"
        } successful`,
        status: "success",
        duration: 3000,
        position: "top",
      });
      setAmount("");
    },
  });

  const handleRadioChange = (value: string | number) => {
    console.log({ value });

    const newAmount = (+value * walletBalance) / 100;
    setAmount(newAmount.toFixed(2));
    formik.setFieldValue("amount", newAmount.toFixed(2));
  };

  return (
    <MotionBox
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
      bg={bgColor}
      borderRadius="xl"
      p={6}
      boxShadow="md"
    >
      <VStack
        as="form"
        spacing={6}
        align="stretch"
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        onSubmit={formik.handleSubmit as any}
      >
        <FormControl>
          <HStack justify="space-between">
            <FormLabel color={textColor}>
              {type.charAt(0).toUpperCase() + type.slice(1)} amount:
            </FormLabel>
            <Text color="gray.500" fontSize="sm">
              Max: {walletBalance} {walletToken}
            </Text>
          </HStack>
          <Input
            type="number"
            placeholder={`${walletBalance}.00`}
            value={amount}
            onChange={(e) => {
              setAmount(e.target.value);
              formik.handleChange(e);
            }}
            borderColor={borderColor}
            _focus={{ borderColor: "blue.500" }}
          />
        </FormControl>

        <CustomRadioGroup
          options={["25", "50", "75", "100"]}
          onChange={handleRadioChange}
          value={amount ? (parseFloat(amount) / walletBalance) * 100 : ""}
        />

        <MotionButton
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          type="submit"
          isLoading={formik.isSubmitting}
          loadingText={
            type === "deposit" ? "Depositing..." : "Submitting request..."
          }
          bgGradient="linear(to-r, blue.400, purple.500)"
          color="white"
          _hover={{ bgGradient: "linear(to-r, blue.500, purple.600)" }}
          isDisabled={!amount}
        >
          {type === "deposit" ? "Deposit" : "Request Withdrawal"}
        </MotionButton>
      </VStack>
    </MotionBox>
  );
};

export const DepositOrWithdrawalBox = ({
  walletBalance,
  walletToken,
}: {
  walletBalance: number;
  walletToken: string;
}) => {
  const [, setActiveTab] = useState(0);
  const bgColor = useColorModeValue("white", "gray.800");
  const borderColor = useColorModeValue("gray.200", "gray.600");

  return (
    <MotionBox
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      bg={bgColor}
      borderRadius="2xl"
      overflow="hidden"
      boxShadow="xl"
      border="1px"
      borderColor={borderColor}
    >
      <Tabs onChange={setActiveTab} isFitted variant="enclosed">
        <TabList>
          <Tab _selected={{ color: "blue.500", borderColor: "blue.500" }}>
            Deposit
          </Tab>
          <Tab _selected={{ color: "blue.500", borderColor: "blue.500" }}>
            Withdraw
          </Tab>
        </TabList>
        <TabPanels>
          <TabPanel>
            <TradeTypeBox
              walletBalance={walletBalance}
              walletToken={walletToken}
              type="deposit"
            />
          </TabPanel>
          <TabPanel>
            <TradeTypeBox
              walletBalance={walletBalance}
              walletToken={walletToken}
              type="withdrawal"
            />
          </TabPanel>
        </TabPanels>
      </Tabs>
    </MotionBox>
  );
};
