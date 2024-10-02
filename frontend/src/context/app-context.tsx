import React, { createContext, ReactNode, useEffect, useState } from "react";
import { useContext } from "react";
import { OktoProvider, BuildType } from "okto-sdk-react";
import { useAppKitConnection } from "@reown/appkit-adapter-solana/react";
import { useAppKitAccount } from "@reown/appkit/react";
import { LAMPORTS_PER_SOL, PublicKey } from "@solana/web3.js";
import { USER_ACCOUNT_TYPE } from "@/types";

export const AppContext = createContext<{
  apiKey: string;
  buildType: BuildType;
  address: string;
  setAddress: (address: string) => void;
  balance: string;
  setBalance: (balance: string) => void;
  balanceSymbol: string;
  setBalanceSymbol: (balanceSymbol: string) => void;
  accountType: USER_ACCOUNT_TYPE;
  setAccountType: (type: USER_ACCOUNT_TYPE) => void;
}>({
  apiKey: "",
  buildType: BuildType.SANDBOX,
  balanceSymbol: "",
  setBalanceSymbol: () => {},
  address: "",
  setAddress: () => {},
  balance: "",
  setBalance: () => {},
  accountType: null,
  setAccountType: () => {},
});

const oktoApiKey = process.env.NEXT_PUBLIC_OKTO_API_KEY!;
export const AppContextProvider = ({ children }: { children: ReactNode }) => {
  const reownAccount = useAppKitAccount();
  const { connection: reownConnection } = useAppKitConnection();

  const [apiKey] = useState(oktoApiKey);
  const [buildType] = useState(BuildType.SANDBOX);
  const [address, setAddress] = useState("");
  const [balance, setBalance] = useState("");
  const [balanceSymbol, setBalanceSymbol] = useState("SOL");
  const [accountType, setAccountType] = useState<USER_ACCOUNT_TYPE>(null);
  useEffect(() => {
    (async () => {
      if (reownAccount.isConnected) {
        setAccountType("WALLET");
        const balResult = await reownConnection?.getBalance(
          new PublicKey(reownAccount.address as string)
        );
        const bal = (balResult || 0) / LAMPORTS_PER_SOL + "";
        setBalance(bal);
        // setBalanceSymbol(reownConnection.get);
        setAddress(reownAccount.address!);
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [reownAccount]);

  return (
    <AppContext.Provider
      value={{
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

export const useAppContext = () => useContext(AppContext);
