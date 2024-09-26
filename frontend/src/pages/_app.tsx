import { createWalletConnectModal } from "@/config/walletConnect";
import { AppChakraProvider } from "@/providers/chakra";
import "@/styles/globals.css";
import type { AppProps } from "next/app";
import { useEffect } from "react";
import { fonts } from "@/lib/fonts";
export default function App({ Component, pageProps }: AppProps) {
  useEffect(() => {
    import("@twa-dev/sdk").then((twa) => {
      const WebApp = twa.default;
      WebApp.MainButton.hide();
      WebApp.expand();
      WebApp.ready();
      WebApp.enableClosingConfirmation();
    });
    createWalletConnectModal();
  }, []);
  return (
    <>
      <style jsx global>
        {`
          :root {
            --font-main: ${fonts.main.style.fontFamily};
          }
        `}
      </style>
      <AppChakraProvider>
        <Component {...pageProps} />
      </AppChakraProvider>
    </>
  );
}
