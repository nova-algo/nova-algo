import { Link } from "@chakra-ui/next-js";
import {
  Box,
  Button,
  HStack,
  Image,
  Text,
  useColorModeValue,
} from "@chakra-ui/react";
import { signIn, useSession, signOut } from "next-auth/react";
import { useEffect, useMemo, useState } from "react";
import { useOkto, OktoContextType } from "okto-sdk-react";

export default function Header() {
  const bgColor = useColorModeValue("blackAlpha.800", "gray.900");
  const [isLoading, setIsLoading] = useState(false);
  const { data: session } = useSession();
  const {
    isLoggedIn,
    authenticate,
    authenticateWithUserId,
    logOut,
    getPortfolio,
    transferTokens,
    getWallets,
    createWallet,
    getSupportedNetworks,
    getSupportedTokens,
    getUserDetails,
    orderHistory,
    getNftOrderDetails,
    showWidgetModal,
    getRawTransactionStatus,
    transferTokensWithJobStatus,
    transferNft,
    transferNftWithJobStatus,
    executeRawTransaction,
    executeRawTransactionWithJobStatus,
    setTheme,
    getTheme,
  } = useOkto() as OktoContextType;
  const idToken = useMemo(
    () =>
      session
        ? //@ts-expect-error id_token not in sesson types
          session?.id_token
        : null,
    [session]
  );

  async function handleAuthenticate(): Promise<any> {
    console.log({ idToken }, "start authenticate");
    if (!idToken) {
      return { result: false, error: "No google login" };
    }
    console.log({ idToken }, "after id token");
    return new Promise((resolve) => {
      authenticate(idToken, (result: any, error: any) => {
        if (result) {
          console.log("Authentication successful");
          resolve({ result: true });
        } else if (error) {
          console.error("Authentication error:", error);
          resolve({ result: false, error });
        }
      });
    });
  }

  async function showLogin() {
    try {
      console.log({ idToken, session });

      setIsLoading(true);
      await signIn("google");

      setIsLoading(false);
    } catch (error) {
      setIsLoading(false);
    }
  }
  useEffect(() => {
    if (session) {
      handleAuthenticate();
    }
  }, [session]);
  async function handleLogout() {
    await signOut();
    logOut();
  }
  async function fetchWallets() {
    const supportedNetworks = await getSupportedNetworks();
    const wallets = await getWallets();
    const supportedTokens = await getSupportedTokens();
    const userDetails = await getUserDetails();
    const portfolio = await getPortfolio();
    console.log({
      wallets,
      supportedNetworks,
      supportedTokens,
      userDetails,
      portfolio,
    });
  }
  return (
    <Box
      backdropFilter={"blur(10px)"}
      px={5}
      py={3}
      pos={"fixed"}
      top={0}
      width={"full"}
      zIndex={1000}
    >
      <HStack
        bg={bgColor}
        rounded={"full"}
        px={{ base: 3, md: 4 }}
        py={{ base: 1, md: 2 }}
        justify={"space-between"}
      >
        <Box>
          <Image
            src="/transparent-app-logo.png"
            alt="Nova Algo logo"
            h={"45px"}
            objectFit={"contain"}
            w={"100px"}
          />
        </Box>
        <HStack as={"nav"} gap={5} fontWeight={500} color={"white"}>
          <Link href={"#"} _hover={{ color: "blue.200" }}>
            Vaults
          </Link>
          <Link href={"#"} _hover={{ color: "blue.200" }}>
            How it works
          </Link>
          <Link href={"#"} _hover={{ color: "blue.200" }}>
            FAQs
          </Link>
        </HStack>
        <Box>
          {session && <Text color={"white"}>Hello {session.user?.name}</Text>}
          <Text color={"white"}>{isLoggedIn + ""}</Text>
          {session && <Button onClick={() => handleLogout()}>Logout</Button>}
          {!session && (
            <Button onClick={() => showLogin()} isLoading={isLoading}>
              Try Nova Algo Free
            </Button>
          )}
          {isLoggedIn && <Button onClick={() => fetchWallets()}>Modal</Button>}
        </Box>
      </HStack>
    </Box>
  );
}
