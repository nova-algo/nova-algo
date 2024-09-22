import { createWeb3Modal, defaultSolanaConfig } from "@web3modal/solana/react";
import { solana, solanaTestnet, solanaDevnet } from "@web3modal/solana/chains";

export const createWalletConnectModal = () => {
  // Setup chains
  const chains = [solana, solanaTestnet, solanaDevnet];

  // Your Reown Cloud project ID
  const projectId = "348a2c1e4e1c8823e911f6f1c137552e";

  // Create metadata
  const metadata = {
    name: "Nova Algo",
    description: "AppKit Example",
    url: "https://reown.com/appkit", // origin must match your domain & subdomain
    icons: ["https://assets.reown.com/reown-profile-pic.png"],
  };

  // Create solanaConfig
  const solanaConfig = defaultSolanaConfig({
    metadata,
    chains,
    projectId,
  });

  // Create modal
  createWeb3Modal({
    solanaConfig,
    chains,
    projectId,
  });
};
