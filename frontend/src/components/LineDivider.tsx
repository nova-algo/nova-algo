import { Box } from "@chakra-ui/react";

export const LineDivider = ({
  styleProps,
}: {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  styleProps?: Record<string, any>;
}) => {
  return (
    <Box
      h={"50px"}
      w={"1"}
      rounded={"full"}
      bg={"gray.200"}
      {...styleProps}
    ></Box>
  );
};
