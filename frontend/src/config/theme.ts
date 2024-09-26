import { extendTheme, theme as chakraTheme } from "@chakra-ui/react";

export const config = {
  initialColorMode: "light",
  useSystemColorMode: false,
};
export const theme = extendTheme({
  config,
  fonts: {
    heading: "var(--font-main)",
    body: "var(--font-main)",
  },
  colors: {
    brand: {},
  },
  components: {
    Button: {
      baseStyle: {
        ...chakraTheme.components.Button.baseStyle,
        borderRadius: "full",
      },
      defaultProps: {
        ...chakraTheme.components.Button.defaultProps,
        colorScheme: "blue",
      },
    },
  },
});
