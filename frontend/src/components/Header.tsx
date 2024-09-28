/* eslint-disable @typescript-eslint/no-explicit-any */
import { Link } from "@chakra-ui/next-js";
import {
  AbsoluteCenter,
  Box,
  Button,
  Divider,
  HStack,
  IconButton,
  Image,
  useColorModeValue,
  useDisclosure,
  VStack,
} from "@chakra-ui/react";
import { signIn, useSession, signOut } from "next-auth/react";
import { useEffect, useMemo, useRef, useState } from "react";
import { useOkto, OktoContextType } from "okto-sdk-react";
import { ResponsivePopoverSheet } from "./SheetOrPopover";
import { FaGoogle } from "react-icons/fa";
import { LuMenu } from "react-icons/lu";

export default function Header() {
  const bgColor = useColorModeValue("#1b1b1b", "gray.900");
  const [isLoading, setIsLoading] = useState(false);
  const { isOpen, onOpen, onClose } = useDisclosure();
  const { data: session } = useSession();
  const triggerRef = useRef<HTMLButtonElement>(null);
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
      // createWallet();
      // getUserDetails();
    }
  }, [session]);

  async function fetchWallets() {
    try {
      const supportedNetworks = await createWallet();

      // await getSupportedNetworks();
      console.log("Supported networks:", supportedNetworks);
    } catch (error) {
      console.error("Error fetching supported networks:", error);
    }

    try {
      const supportedTokens = await getSupportedTokens();
      console.log("Supported tokens:", supportedTokens);
    } catch (error) {
      console.error("Error fetching supported tokens:", error);
    }

    try {
      const wallets = await getWallets();
      console.log("Wallets:", wallets);
    } catch (error) {
      console.error("Error fetching wallets:", error);
    }

    try {
      const userDetails = await getUserDetails();
      console.log("User details:", userDetails);
    } catch (error) {
      console.error("Error fetching user details:", error);
    }

    try {
      const portfolio = await getPortfolio();
      console.log("Portfolio:", portfolio);
    } catch (error) {
      console.error("Error fetching portfolio:", error);
    }
  }
  async function handleLogout() {
    await signOut();
    logOut();
  }
  return (
    <>
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
          py={2}
          justify={"space-between"}
        >
          <Box>
            <Image
              src="/transparent-app-logo.png"
              alt="Nova Algo logo"
              h={"40px"}
              objectFit={"contain"}
              w={"100px"}
            />
          </Box>
          <HStack
            as={"nav"}
            gap={5}
            fontWeight={500}
            color={"white"}
            hideBelow={"md"}
          >
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
            <HStack gap={3}>
              {session && (
                <Button onClick={() => fetchWallets()} ref={triggerRef}>
                  Logout
                </Button>
              )}
              {!session && (
                <ResponsivePopoverSheet
                  title=""
                  isOpen={isOpen}
                  onClose={onClose}
                  onOpen={onOpen}
                  trigger={
                    <Button
                      onClick={() => onOpen()}
                      size={{ base: "sm", md: "md" }}
                      isLoading={isLoading}
                    >
                      Try Nova Algo Free
                    </Button>
                  }
                  content={
                    <>
                      <VStack>
                        <w3m-button />

                        <Box position="relative" padding="4">
                          <Divider />
                          <AbsoluteCenter bg="white" px="4">
                            or
                          </AbsoluteCenter>
                        </Box>
                        <Button
                          variant={"outline"}
                          leftIcon={<FaGoogle />}
                          onClick={() => showLogin()}
                        >
                          Continue with Google
                        </Button>
                      </VStack>
                    </>
                  }
                />
              )}
              <Box hideFrom={"md"}>
                <IconButton
                  size={"sm"}
                  icon={<LuMenu />}
                  aria-label="toggle menu"
                  color={"white"}
                  variant={"outline"}
                  _hover={{ color: "blue.200" }}
                />
              </Box>
            </HStack>
          </Box>
        </HStack>
      </Box>
    </>
  );
}
