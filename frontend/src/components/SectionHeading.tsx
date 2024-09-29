/* eslint-disable @typescript-eslint/no-explicit-any */

import { HStack, Text } from "@chakra-ui/react";

export default function SectionHeading({
  title,
  containerStyleProps,
  textStyleProps,
  hideBorder,
}: {
  title: string;
  hideBorder?: boolean;
  containerStyleProps?: Record<string, any>;
  textStyleProps?: Record<string, any>;
}) {
  return (
    <HStack
      my={5}
      pos={"relative"}
      pb={2}
      {...(!hideBorder && {
        _before: {
          content: `''`,
          w: "50px",
          h: "3px",
          rounded: "full",
          bg: "orange.500",
          pos: "absolute",
          bottom: "0",
          left: 0,
        },
      })}
      {...containerStyleProps}
    >
      <Text
        as={"span"}
        fontSize={{ base: "18px", md: "22px" }}
        fontWeight={"bold"}
        {...textStyleProps}
      >
        {title}
      </Text>
    </HStack>
  );
}
