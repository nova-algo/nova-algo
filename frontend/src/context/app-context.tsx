import React, { createContext, ReactNode, useEffect, useState } from "react";
import { useContext } from "react";
import { OktoProvider, BuildType, WalletData } from "okto-sdk-react";
import { Connection, clusterApiUrl } from "@solana/web3.js";
import { useAppKitConnection } from "@reown/appkit-adapter-solana/react";
import { AppKit, useAppKitAccount } from "@reown/appkit/react";
import { LAMPORTS_PER_SOL, PublicKey } from "@solana/web3.js";
import { NextAuthSession, USER_ACCOUNT_TYPE } from "@/types";
import { useSession } from "next-auth/react";
import { createWalletConnectModal } from "@/config/walletConnect";
import { useRouter } from "next/router";
const connection = new Connection(clusterApiUrl("devnet"), "confirmed");
export const AppContext = createContext<{
  apiKey: string;
  buildType: BuildType;
  idToken: string;
  setIdToken: (token: string) => void;
  address: string;
  setAddress: (address: string) => void;
  balance: string;
  setBalance: (balance: string) => void;
  balanceSymbol: string;
  setBalanceSymbol: (balanceSymbol: string) => void;
  accountType: USER_ACCOUNT_TYPE;
  setAccountType: (type: USER_ACCOUNT_TYPE) => void;
  appkitModal: AppKit | null;
  isAuthenticated: boolean;
  setIsAuthenticated: (isAuth: boolean) => void;
}>({
  apiKey: "",
  isAuthenticated: false,
  setIsAuthenticated: () => {},
  buildType: BuildType.SANDBOX,
  idToken: "",
  setIdToken: () => {},
  balanceSymbol: "",
  setBalanceSymbol: () => {},
  address: "",
  setAddress: () => {},
  balance: "",
  setBalance: () => {},
  accountType: null,
  setAccountType: () => {},
  appkitModal: null,
});

const oktoApiKey = process.env.NEXT_PUBLIC_OKTO_API_KEY!;
export const AppContextProvider = ({ children }: { children: ReactNode }) => {
  const reownAccount = useAppKitAccount();
  const { data: session } = useNextAuthSession();
  const { connection: reownConnection } = useAppKitConnection();
  const [idToken, setIdToken] = useState("");
  const [apiKey] = useState(oktoApiKey);
  const [buildType] = useState(BuildType.SANDBOX);
  const [address, setAddress] = useState("");
  const [balance, setBalance] = useState("");
  const [balanceSymbol, setBalanceSymbol] = useState("SOL");
  const [accountType, setAccountType] = useState<USER_ACCOUNT_TYPE>(null);
  const appkitModal = createWalletConnectModal();
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  useEffect(() => {
    (async () => {
      if (reownAccount.isConnected) {
        setIsAuthenticated(true);
        const publicKey = new PublicKey(reownAccount.address as string);
        setAccountType("WALLET");
        try {
          const balResult = await reownConnection?.getBalance(publicKey);
          const bal = (balResult || 0) / LAMPORTS_PER_SOL + "";
          setBalance(bal);
        } catch (error) {}
        // setBalanceSymbol(reownConnection.get);
        setAddress(reownAccount.address!);
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [reownAccount]);
  useEffect(() => {
    const authDetails = JSON.parse(
      localStorage.getItem("AUTH_DETAILS") || "{}"
    );
    (async () => {
      if (session) {
        setAccountType("GOOGLE");
        setIdToken(session?.id_token as string);
        const { wallets } = await fetch(
          "https://sandbox-api.okto.tech/api/v1/wallet",
          {
            headers: {
              "x-api-key": oktoApiKey,
              Authorization: `Bearer ${authDetails.authToken}`,
            },
          }
        ).then(async (res) => {
          const result = await res.json();
          return result.data as WalletData;
        });
        const solWallet = wallets.find(
          (w) =>
            w.network_name.toLowerCase() === "solana" ||
            w.network_name.toLowerCase() === "solana_devnet"
        );
        if (solWallet) {
          setAddress(solWallet.address);
        } else {
          setAddress("");
        }
      }
    })();
  }, [session]);
  useEffect(() => {
    (async () => {
      if (address && accountType == "GOOGLE") {
        setIsAuthenticated(true);
        const publicKey = new PublicKey(address as string);

        try {
          const balResult = await connection?.getBalance(publicKey);

          const bal = (balResult || 0) / LAMPORTS_PER_SOL + "";
          setBalance(bal);
        } catch (error) {}
        // setBalanceSymbol(reownConnection.get);
        // setAddress(reownAccount.address!);
      } else {
        setIsAuthenticated(false);
      }
    })();
  }, [address, accountType]);
  const router = useRouter();
  useEffect(() => {
    if (isAuthenticated) {
      router.push("/dashboard");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated]);
  return (
    <AppContext.Provider
      value={{
        isAuthenticated,
        setIsAuthenticated,
        appkitModal,
        idToken,
        setIdToken,
        apiKey,
        buildType,
        address,
        setAddress,
        balance,
        setBalance,
        balanceSymbol,
        setBalanceSymbol,
        accountType,
        setAccountType,
      }}
    >
      <OktoProvider apiKey={apiKey} buildType={buildType}>
        {children}
      </OktoProvider>
    </AppContext.Provider>
  );
};
// eslint-disable-next-line @typescript-eslint/no-explicit-any
type UpdateSession = (data?: any) => Promise<NextAuthSession | null>;

export const useAppContext = () => useContext(AppContext);
export const useNextAuthSession = () =>
  useSession() as {
    data: NextAuthSession | null;
    status: "authenticated" | "loading" | "unauthenticated";
    update: UpdateSession;
  };
