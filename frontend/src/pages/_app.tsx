import { createWalletConnectModal } from "@/config/walletConnect";
import { AppChakraProvider } from "@/providers/chakra";
import "@/styles/globals.css";
import type { AppProps } from "next/app";
import WebApp from "@twa-dev/sdk";

WebApp.MainButton.hide();
// Expand the Telegram Mini App to full screen
WebApp.expand();
// Initialize the Telegram Mini App SDK
WebApp.ready();
// Enable the closing confirmation
WebApp.enableClosingConfirmation();

// Create the WalletConnect modal
createWalletConnectModal();
export default function App({ Component, pageProps }: AppProps) {
  return (
    <AppChakraProvider>
      <Component {...pageProps} />
    </AppChakraProvider>
  );
}
