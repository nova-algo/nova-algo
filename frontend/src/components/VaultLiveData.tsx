import React, { useState } from "react";
import {
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  TableContainer,
  Tabs,
  TabList,
  Tab,
  TabPanels,
  TabPanel,
  Box,
  Text,
  useColorModeValue,
  Badge,
  Button,
  Icon,
} from "@chakra-ui/react";
import { LuExternalLink, LuCircle } from "react-icons/lu";
import { Link } from "@chakra-ui/next-js";

const VaultLiveData = () => {
  const [tabIndex, setTabIndex] = useState(0);
  const bgColor = useColorModeValue("white", "gray.800");
  const textColor = useColorModeValue("gray.800", "white");
  const borderColor = useColorModeValue("gray.200", "gray.700");

  const balancesData = [
    {
      market: "USDC",
      balance: "-6,555,417.746891 USDC",
      notional: "-$6,555,417.746891",
      liqPrice: "$2.723244",
    },
    {
      market: "SOL",
      balance: "81,083.411126634 SOL",
      notional: "$12,135,437.755758",
      liqPrice: "$253.445615",
    },
    {
      market: "JitoSOL",
      balance: "61,218.4339678 JitoSOL",
      notional: "$10,467,983.550947",
      liqPrice: "-",
    },
    {
      market: "PYUSD",
      balance: "670,079.989703 PYUSD",
      notional: "$669,819.998666",
      liqPrice: "-",
    },
  ];

  const positionsData = [
    {
      market: "SOL-PERP",
      size: "158,225 SOL",
      notional: "$23,684,908.73",
      entryIndex: "$141.104451",
      pnl: "-$1,358,525.627121",
      pnlPercentage: "-6.084%",
      liqPrice: "$263.614617",
      type: "SHORT",
    },
  ];

  const ordersData = [
    {
      market: "SOL-PERP",
      type: "LIMIT",
      filled: "0.0",
      size: "105.0",
      limit: "$149.687",
    },
    {
      market: "SOL-PERP",
      type: "LIMIT",
      filled: "0.0",
      size: "157.5",
      limit: "$149.642",
    },
    {
      market: "SOL-PERP",
      type: "LIMIT",
      filled: "0.0",
      size: "236.2",
      limit: "$149.598",
    },
  ];

  const renderBalancesTable = () => (
    <TableContainer>
      <Table variant="simple">
        <Thead>
          <Tr>
            <Th>Market</Th>
            <Th>Balance</Th>
            <Th>Notional</Th>
            <Th>Liq. Price</Th>
          </Tr>
        </Thead>
        <Tbody>
          {balancesData.map((item, index) => (
            <Tr key={index}>
              <Td>
                <Icon
                  as={LuCircle}
                  color={
                    item.market === "USDC"
                      ? "blue.500"
                      : item.market === "SOL"
                      ? "purple.500"
                      : "green.500"
                  }
                  mr={2}
                />
                {item.market}
              </Td>
              <Td>{item.balance}</Td>
              <Td>{item.notional}</Td>
              <Td>{item.liqPrice}</Td>
            </Tr>
          ))}
        </Tbody>
      </Table>
    </TableContainer>
  );

  const renderPositionsTable = () => (
    <TableContainer>
      <Table variant="simple">
        <Thead>
          <Tr>
            <Th>Market</Th>
            <Th>Size</Th>
            <Th>Entry/Index</Th>
            <Th>P&L</Th>
            <Th>Liq. Price</Th>
          </Tr>
        </Thead>
        <Tbody>
          {positionsData.map((item, index) => (
            <Tr key={index}>
              <Td>
                <Text>{item.market}</Text>
                <Badge colorScheme="red">{item.type}</Badge>
              </Td>
              <Td>
                <Text>{item.size}</Text>
                <Text fontSize="sm" color="gray.500">
                  {item.notional}
                </Text>
              </Td>
              <Td>{item.entryIndex}</Td>
              <Td>
                <Text color="red.500">{item.pnl}</Text>
                <Text fontSize="sm" color="red.500">
                  {item.pnlPercentage}
                </Text>
              </Td>
              <Td>{item.liqPrice}</Td>
            </Tr>
          ))}
        </Tbody>
      </Table>
    </TableContainer>
  );

  const renderOrdersTable = () => (
    <TableContainer>
      <Table variant="simple">
        <Thead>
          <Tr>
            <Th>Market</Th>
            <Th>Type</Th>
            <Th>Filled / Size</Th>
            <Th>Trigger / Limit</Th>
          </Tr>
        </Thead>
        <Tbody>
          {ordersData.map((item, index) => (
            <Tr key={index}>
              <Td>
                <Text>{item.market}</Text>
                <Badge colorScheme="green">LONG</Badge>
              </Td>
              <Td>{item.type}</Td>
              <Td>{`${item.filled} / ${item.size}`}</Td>
              <Td>{`- / ${item.limit}`}</Td>
            </Tr>
          ))}
        </Tbody>
      </Table>
    </TableContainer>
  );
  const tabStyles = {
    rounded: "full",
    _hover: { bg: "blue.400", color: "blue.50" },
    _selected: {
      borderColor: "blue.500",
    },
  };
  return (
    <Box
      bg={bgColor}
      color={textColor}
      borderRadius="24px"
      borderWidth="1px"
      borderColor={borderColor}
    >
      <Tabs index={tabIndex} onChange={setTabIndex} variant="enclosed">
        <TabList gap={2} flexDir={{ base: "column", sm: "row" }}>
          <Tab {...tabStyles}>
            Balances{" "}
            <Badge ml={2} colorScheme="blue">
              5
            </Badge>
          </Tab>
          <Tab {...tabStyles}>
            Positions{" "}
            <Badge ml={2} colorScheme="blue">
              1
            </Badge>
          </Tab>
          <Tab {...tabStyles}>
            Orders{" "}
            <Badge ml={2} colorScheme="blue">
              27
            </Badge>
          </Tab>
        </TabList>
        <TabPanels>
          <TabPanel>{renderBalancesTable()}</TabPanel>
          <TabPanel>{renderPositionsTable()}</TabPanel>
          <TabPanel>{renderOrdersTable()}</TabPanel>
        </TabPanels>
      </Tabs>
      <Box p={4}>
        <Button
          as={Link}
          href={"#"}
          isExternal
          rightIcon={<LuExternalLink />}
          variant="outline"
          size="sm"
        >
          View Vault Activity on Drift
        </Button>
      </Box>
    </Box>
  );
};

export default VaultLiveData;
