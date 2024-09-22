import { theme } from "@/config/theme";
import { ChakraProvider } from "@chakra-ui/react";

export const AppChakraProvider = ({
  children,
}: {
  children: React.ReactNode;
}) => {
  return <ChakraProvider theme={theme}>{children}</ChakraProvider>;
};
