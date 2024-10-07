import { theme } from "@/config/theme";
import { useAppContext, useNextAuthSession } from "@/context/app-context";
import { ChakraProvider } from "@chakra-ui/react";
import { OktoContextType, useOkto } from "okto-sdk-react";
import { useEffect } from "react";

export const AppChakraProvider = ({
  children,
}: {
  children: React.ReactNode;
}) => {
  const { getWallets } = useOkto() as OktoContextType;
  const { data: session, status } = useNextAuthSession();
  const { setAccountType, setIdToken, setAddress } = useAppContext();
  useEffect(() => {
    (async () => {
      if (session && status !== "loading") {
        setAccountType("GOOGLE");
        setIdToken(session?.id_token as string);

        try {
          const { wallets } = await getWallets();

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
        } catch (error) {}
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [session, status]);
  return <ChakraProvider theme={theme}>{children}</ChakraProvider>;
};
