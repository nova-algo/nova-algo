import { createAppKit } from "@reown/appkit/react";
import { SolanaAdapter } from "@reown/appkit-adapter-solana/react";
import { solana, solanaTestnet, solanaDevnet } from "@reown/appkit/networks";
import {
  PhantomWalletAdapter,
  SolflareWalletAdapter,
} from "@solana/wallet-adapter-wallets";

// 0. Set up Solana Adapter
const solanaWeb3JsAdapter = new SolanaAdapter({
  wallets: [new PhantomWalletAdapter(), new SolflareWalletAdapter()],
});
export const createWalletConnectModal = () => {
  // Your Reown Cloud project ID
  const projectId = process.env.NEXT_PUBLIC_REOWN_PROJECT_ID!;

  // 2. Create a metadata object - optional
  const metadata = {
    name: "Nova Algo",
    description: "Nova AI-powered Algo Trading",
    url: process.env.NEXT_PUBLIC_APP_URL!, // origin must match your domain & subdomain
    icons: ["https://assets.reown.com/reown-profile-pic.png"],
  };

  // 3. Create modal
  return createAppKit({
    adapters: [solanaWeb3JsAdapter],
    networks: [solana, solanaTestnet, solanaDevnet],
    metadata: metadata,
    themeMode: "light",
    themeVariables: {
      "--w3m-z-index": 3000,
    },
    projectId,
    features: {
      email: false,
      socials: [],
      analytics: true, // Optional - defaults to your Cloud configuration
    },
  });
};
