import { createWalletConnectModal } from "@/config/walletConnect";
import { AppChakraProvider } from "@/providers/chakra";
import "@/styles/globals.css";
import type { AppProps } from "next/app";
import { useEffect } from "react";

export default function App({ Component, pageProps }: AppProps) {
  useEffect(() => {
    import("@twa-dev/sdk").then((twa) => {
      const WebApp = twa.default;
      console.log("WebApp", WebApp);
      WebApp.MainButton.hide();
      WebApp.expand();
      WebApp.ready();
      WebApp.enableClosingConfirmation();
    });
    createWalletConnectModal();
  }, []);
  return (
    <AppChakraProvider>
      <Component {...pageProps} />
    </AppChakraProvider>
  );
}
