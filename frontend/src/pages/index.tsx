import Homepage from "@/components/Homepage";
import WalletConnectModal from "@/components/WalletConnectModal";
import { useEffect, useState } from "react";

export default function Home() {
  const [isReady, setIsReady] = useState(false);
  useEffect(() => {
    setIsReady(true);
  }, []);
  if (!isReady) return <div>Loading...</div>;
  return <Homepage />;
}
