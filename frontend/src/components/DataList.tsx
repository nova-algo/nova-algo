import { HStack, List, ListItem, Stack, Text } from "@chakra-ui/react";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export default function DataList({ data = {} }: { data: Record<string, any> }) {
  return (
    <List as={Stack} gap={3}>
      {Object.keys(data).map((key) => (
        <ListItem
          key={key}
          as={HStack}
          fontWeight={"500"}
          justify={"space-between"}
          fontSize={{ base: "16px", md: "18px" }}
        >
          <Text
            as={"span"}
            color={"gray.500"}
            fontSize={{ base: "17px", md: "18px" }}
            textAlign={"left"}
          >
            {key}
          </Text>
          <Text as={"span"} textAlign={"right"}>
            {data[key as keyof typeof data]}
          </Text>
        </ListItem>
      ))}
    </List>
  );
}
