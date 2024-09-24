import { extendTheme } from "@chakra-ui/react";

export const config = {
  initialColorMode: "light",
  useSystemColorMode: false,
};
export const theme = extendTheme({
  config,
  colors: {
    brand: {},
  },
});
