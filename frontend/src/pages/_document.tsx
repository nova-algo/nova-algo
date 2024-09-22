import { theme } from "@/config/theme";
import { ColorModeScript } from "@chakra-ui/react";
import { Html, Head, Main, NextScript } from "next/document";

export default function Document() {
  return (
    <Html lang="en">
      <Head />
      <body className="antialiased">
        <Main />
        <NextScript />
        <ColorModeScript initialColorMode={theme.config.initialColorMode} />
      </body>
    </Html>
  );
}
