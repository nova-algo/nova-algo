import React, { createContext, ReactNode, useEffect, useState } from "react";
import { useContext } from "react";
import { OktoProvider, BuildType } from "okto-sdk-react";
import * as reown from "@reown/appkit";

export const AppContext = createContext<{
  apiKey: string;
  buildType: BuildType;
  address: string;
  setAddress: (address: string) => void;
  balance: string;
  setBalance: (balance: string) => void;
  balanceSymbol: string;
  setBalanceSymbol: (balanceSymbol: string) => void;
}>({
  apiKey: "",
  buildType: BuildType.SANDBOX,
  balanceSymbol: "",
  setBalanceSymbol: () => {},
  address: "",
  setAddress: () => {},
  balance: "",
  setBalance: () => {},
});

const oktoApiKey = process.env.NEXT_PUBLIC_OKTO_API_KEY!;
export const AppContextProvider = ({ children }: { children: ReactNode }) => {
  const [apiKey] = useState(oktoApiKey);
  const [buildType] = useState(BuildType.SANDBOX);
  const [address, setAddress] = useState("");
  const [balance, setBalance] = useState("");
  const [balanceSymbol, setBalanceSymbol] = useState("SOL");
  useEffect(() => {
    setBalance(reown.AccountController.state.balance!);
    setBalanceSymbol(reown.AccountController.state.balanceSymbol!);
    setAddress(reown.AccountController.state.address!);
  }, []);

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
      }}
    >
      <OktoProvider apiKey={apiKey} buildType={buildType}>
        {children}
      </OktoProvider>
    </AppContext.Provider>
  );
};

export const useAppContext = () => useContext(AppContext);
