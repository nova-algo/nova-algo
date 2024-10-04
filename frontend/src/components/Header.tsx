/* eslint-disable @typescript-eslint/no-explicit-any */

import {
  AbsoluteCenter,
  Box,
  Button,
  DarkMode,
  Divider,
  Drawer,
  DrawerCloseButton,
  DrawerContent,
  DrawerHeader,
  DrawerOverlay,
  HStack,
  IconButton,
  Image,
  Text,
  useBreakpointValue,
  useColorModeValue,
  useDisclosure,
  VStack,
} from "@chakra-ui/react";
import { signOut } from "next-auth/react";
import { useEffect } from "react";
import { useOkto, OktoContextType, WalletData } from "okto-sdk-react";
import { ResponsiveModalSheet } from "./SheetOrModal";
import { LuMenu } from "react-icons/lu";
import Gradient3DBackground from "./GradientBg";
import { shortenAddress } from "@/utils";
import Navbar from "./Navbar";
import { Link } from "@chakra-ui/next-js";
import { useAppContext, useNextAuthSession } from "@/context/app-context";
import { GoogleLogin } from "./GoogleLogin";

export default function Header() {
  const { address, idToken, setAddress, appkitModal } = useAppContext();
  const logo = useBreakpointValue({
    base: "/images/mobile-logo-white.png",
    md: "/images/desktop-logo-white.png",
  });
  // const { disconnect } = useDisconnect();
  const bgColor = useColorModeValue("#1b1b1b", "gray.900");
  const { isOpen, onOpen, onClose } = useDisclosure();
  const {
    isOpen: isNavbarOpen,
    onOpen: onNavbarOpen,
    onClose: onNavbarClose,
  } = useDisclosure();
  const { data: session } = useNextAuthSession();
  const {
    isLoggedIn,
    authenticate,
    logOut,
    // showWidgetModal,
    // createWallet,
    // getPortfolio,
    // getSupportedTokens,
    // getWallets,
    // getUserDetails,
  } = useOkto() as OktoContextType;

  async function handleAuthenticate(): Promise<any> {
    console.log({ idToken }, "start authenticate");
    if (!idToken) {
      return { result: false, error: "No google login" };
    }

    return new Promise((resolve) => {
      authenticate(idToken, (result: any, error: any) => {
        if (result) {
          resolve({ result: true });
        } else if (error) {
          resolve({ result: false, error });
        }
      });
    });
  }

  const createWallet = async (authToken: string) => {
    const baseUrl = "https://sandbox-api.okto.tech";
    const apiKey = process.env.NEXT_PUBLIC_OKTO_API_KEY;

    try {
      const response = await fetch(`${baseUrl}/api/v1/wallet`, {
        method: "POST",
        headers: {
          "x-api-key": apiKey || "",
          accept: "application/json",
          Authorization: `Bearer ${authToken}`,
        },
      });

      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }

      const data = await response.json();
      console.log("Wallet created:", data);
      return data.data as WalletData;
    } catch (error) {
      console.error("Failed to create wallet:", error);
      throw error;
    }
  };
  useEffect(() => {
    let authToken = "";
    (async () => {
      if (idToken && !isLoggedIn) {
        handleAuthenticate().then(async () => {
          if (typeof window !== "undefined") {
            const authDetails = JSON.parse(
              localStorage.getItem("AUTH_DETAILS") || "{}"
            );
            authToken = authDetails.authToken;
          }
          const { wallets } = await createWallet(authToken);
          console.log({ wallets });

          if (wallets.length > 0) {
            const solWallet = wallets.find(
              (wallet) => wallet.network_name.toLowerCase() === "solana"
            );
            setAddress(solWallet?.address as string);
          }
        });

        // fetchWallets();
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [idToken]);

  // async function fetchWallets() {
  //   try {
  //     const createdWallet = await createWallet();

  //     // await getSupportedNetworks();
  //     console.log("Created wallet:", createdWallet);
  //   } catch (error) {
  //     console.error("Error creating wallet :", error);
  //   }

  //   try {
  //     const supportedTokens = await getSupportedTokens();
  //     console.log("Supported tokens:", supportedTokens);
  //   } catch (error) {
  //     console.error("Error fetching supported tokens:", error);
  //   }

  //   try {
  //     const wallets = await getWallets();
  //     console.log("Wallets:", wallets);
  //   } catch (error) {
  //     console.error("Error fetching wallets:", error);
  //   }

  //   try {
  //     const userDetails = await getUserDetails();
  //     console.log("User details:", userDetails);
  //   } catch (error) {
  //     console.error("Error fetching user details:", error);
  //   }

  //   try {
  //     const portfolio = await getPortfolio();
  //     console.log("Portfolio:", portfolio);
  //   } catch (error) {
  //     console.error("Error fetching portfolio:", error);
  //   }
  // }
  async function handleLogout() {
    // const s = appkitModal?.getIsConnectedState();

    await appkitModal?.adapter?.connectionControllerClient
      ?.disconnect()
      .then(() => setAddress(""));

    session && (await signOut());
    isLoggedIn && logOut();
  }

  return (
    <>
      <Box
        backdropFilter={"blur(10px)"}
        px={{ base: 2, md: 5 }}
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
          <Box as={Link} href={"/"} textDecoration={"none"}>
            <Image
              src={logo}
              alt="Nova Algo logo"
              h={"40px"}
              objectFit={"contain"}
              maxW={"100px"}
            />
          </Box>
          {/* <Button onClick={async () => await fetchWallets()}>
            create wallet
          </Button> */}
          <Box hideBelow={"md"}>
            <DarkMode>
              <Navbar />
            </DarkMode>
          </Box>
          <Box>
            <HStack gap={3}>
              {(session || address) && (
                <HStack>
                  <DarkMode>
                    <Button
                      size={{ base: "sm", md: "md" }}
                      gap={2}
                      variant={"outline"}
                      colorScheme="gray"
                      onClick={async () => await handleLogout()}
                    >
                      <Gradient3DBackground />
                      <Text>{shortenAddress(address || "")}</Text>
                    </Button>
                  </DarkMode>
                </HStack>
              )}
              {!session && !address && (
                <>
                  {" "}
                  <Button
                    onClick={() => onOpen()}
                    size={{ base: "sm", md: "md" }}
                  >
                    Try Nova Algo Free
                  </Button>
                  <ResponsiveModalSheet
                    title=""
                    isOpen={isOpen}
                    onClose={onClose}
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
                          <GoogleLogin />
                        </VStack>
                      </>
                    }
                  />
                </>
              )}
              <Box hideFrom={"md"}>
                <IconButton
                  onClick={() => onNavbarOpen()}
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
      <Drawer isOpen={isNavbarOpen} onClose={onNavbarClose}>
        <DrawerOverlay />
        <DrawerContent>
          <DrawerCloseButton />
          <DrawerHeader></DrawerHeader>
          <Box pt={10}>
            <Navbar />
          </Box>
        </DrawerContent>
      </Drawer>
    </>
  );
}
