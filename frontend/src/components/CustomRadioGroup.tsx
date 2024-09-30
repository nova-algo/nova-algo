import { Button, HStack, Text, useColorModeValue } from "@chakra-ui/react";

export const CustomRadioGroup = ({
  options,
  onChange,
  value,
  prefix = "",
}: {
  options: string[];
  onChange: (val: string) => void;
  value: string | number;
  prefix?: string;
}) => {
  const bgColor = useColorModeValue("white", "gray.800");
  const activeColor = useColorModeValue("blue.500", "blue.300");

  const val = value + "";
  return (
    <HStack
      spacing={0}
      border="1px"
      borderColor="gray.200"
      borderRadius="full"
      overflow="hidden"
    >
      {options.map((option) => (
        <Button
          key={option}
          onClick={() => onChange(option)}
          bg={val === option ? activeColor : bgColor}
          color={val === option ? "white" : "gray.600"}
          _hover={{ bg: val === option ? activeColor : "gray.100" }}
          borderRadius="0"
          flexGrow={1}
          flexShrink={0}
        >
          <Text>{option === "100" ? "MAX" : `${option}${prefix}`}</Text>
        </Button>
      ))}
    </HStack>
  );
};
