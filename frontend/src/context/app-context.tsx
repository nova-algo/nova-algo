import React, { createContext, ReactNode, useState } from "react";
import { useContext } from "react";
import { OktoProvider, BuildType } from "okto-sdk-react";
// Create a context with a default value
export const AppContext = createContext({});

const oktoApiKey = process.env.NEXT_PUBLIC_OKTO_API_KEY!;
export const AppContextProvider = ({ children }: { children: ReactNode }) => {
  const [apiKey, setApiKey] = useState(oktoApiKey);
  const [buildType, setBuildType] = useState(BuildType.SANDBOX);

  return (
    <AppContext.Provider value={{ apiKey, setApiKey, buildType, setBuildType }}>
      <OktoProvider apiKey={apiKey} buildType={buildType}>
        {children}
      </OktoProvider>
    </AppContext.Provider>
  );
};

export const useAppContext = () => useContext(AppContext);
