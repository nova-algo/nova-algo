import React, { useState, useMemo } from "react";
import {
  Box,
  Button,
  HStack,
  Menu,
  MenuButton,
  MenuItem,
  MenuList,
  Text,
  useColorModeValue,
} from "@chakra-ui/react";
import { format, subDays } from "date-fns";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  TooltipProps,
} from "recharts";
import { motion } from "framer-motion";
import { BsChevronDown } from "react-icons/bs";
import { CustomRadioGroup } from "./CustomRadioGroup";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const MotionBox = motion.create(Box as any);

interface DataPoint {
  date: string;
  value: number;
}

interface TimeRange {
  value: string;
  label: string;
}

interface CustomTooltipProps extends TooltipProps<number, string> {
  active?: boolean;
  payload?: { value: number }[];
  label?: string;
}

const CustomTooltip: React.FC<CustomTooltipProps> = ({
  active,
  payload,
  label,
}) => {
  const bgColor = useColorModeValue("white", "gray.800");
  const textColor = useColorModeValue("gray.800", "white");

  if (active && payload && payload.length) {
    return (
      <Box bg={bgColor} p={3} borderRadius="md" boxShadow="lg">
        <Text fontWeight="bold" color={textColor}>
          {label}
        </Text>
        <Text color="blue.500">Value: {payload[0].value.toFixed(2)}</Text>
      </Box>
    );
  }
  return null;
};

const generateMockData = (days: number): DataPoint[] => {
  const data: DataPoint[] = [];
  const now = new Date();
  for (let i = days - 1; i >= 0; i--) {
    const date = subDays(now, i);
    data.push({
      date: format(date, "dd/MM"),
      value: Math.random() * 1000 + 500,
    });
  }
  return data;
};

const VaultChart: React.FC = () => {
  const [timeRange, setTimeRange] = useState<TimeRange>({
    value: "7",
    label: "7 days",
  });
  const bgColor = useColorModeValue("white", "gray.800");
  const textColor = useColorModeValue("gray.800", "white");
  const chartColor = useColorModeValue("blue.500", "blue.300");
  const [radioValue, setSelectedRadioValue] = useState("P&L");
  const data = useMemo(() => {
    const days = timeRange.value === "all" ? 365 : parseInt(timeRange.value);
    return generateMockData(days);
  }, [timeRange]);

  const handleTimeRangeChange = (value: string, label: string): void => {
    setTimeRange({ value, label });
  };
  const handleRadioGroupChange = (val: string) => {
    setSelectedRadioValue(val);
  };
  return (
    <MotionBox
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      bg={bgColor}
      borderRadius="xl"
      py={{ base: 4, md: 5 }}
      px={{ base: 2, md: 4, lg: 6 }}
      boxShadow="lg"
    >
      <HStack justifyContent="space-between" mb={4} wrap={"wrap"} spacing={5}>
        <Text fontSize="2xl" fontWeight="bold" color={textColor}>
          Vault Performance
        </Text>
        <HStack spacing={{ base: 4, md: 5 }}>
          <CustomRadioGroup
            onChange={handleRadioGroupChange}
            value={radioValue}
            options={["P&L", "Vault Balance"]}
          />
          <Menu>
            <MenuButton
              size={{ base: "sm", md: "md" }}
              as={Button}
              rightIcon={<BsChevronDown />}
              variant="outline"
            >
              {timeRange.label}
            </MenuButton>
            <MenuList>
              {[
                { value: "7", label: "7 days" },
                { value: "30", label: "30 days" },
                { value: "all", label: "All time" },
              ].map((item) => (
                <MenuItem
                  key={item.value}
                  onClick={() => handleTimeRangeChange(item.value, item.label)}
                >
                  {item.label}
                </MenuItem>
              ))}
            </MenuList>
          </Menu>
        </HStack>
      </HStack>
      <Box height="400px">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart
            data={data}
            margin={{ top: 10, right: 0, left: 0, bottom: 0 }}
          >
            <defs>
              <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={chartColor} stopOpacity={0.8} />
                <stop offset="95%" stopColor={chartColor} stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid
              strokeDasharray="3 3"
              stroke={useColorModeValue("gray.200", "gray.600")}
            />
            <XAxis
              dataKey="date"
              stroke={textColor}
              tick={{ fill: textColor }}
            />
            <YAxis stroke={textColor} tick={{ fill: textColor }} />
            <Tooltip content={<CustomTooltip />} />
            <Area
              type="monotone"
              dataKey="value"
              stroke={chartColor}
              fillOpacity={1}
              fill="url(#colorValue)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </Box>
    </MotionBox>
  );
};

export default VaultChart;
