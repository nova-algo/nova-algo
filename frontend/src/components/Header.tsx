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
import { useSession, signOut } from "next-auth/react";
import { useEffect, useMemo } from "react";
import { useOkto, OktoContextType } from "okto-sdk-react";
import { ResponsiveModalSheet } from "./SheetOrModal";
import { FaGoogle } from "react-icons/fa";
import { LuMenu } from "react-icons/lu";

import Gradient3DBackground from "./GradientBg";
import { shortenAddress } from "@/utils";
import { useDisconnect } from "@web3modal/solana/react";
import Navbar from "./Navbar";
import { Link } from "@chakra-ui/next-js";

import { useGoogleLogin } from "@/hooks";
import { useAppContext } from "@/context/app-context";

export default function Header() {
  const { address } = useAppContext();
  const { isLoading, handleLogin } = useGoogleLogin();
 
  const logo = useBreakpointValue({
    base: "/images/mobile-logo-white.png",
    md: "/images/desktop-logo-white.png",
  });
  const { disconnect } = useDisconnect();
  const bgColor = useColorModeValue("#1b1b1b", "gray.900");
  const { isOpen, onOpen, onClose } = useDisclosure();
  const {
    isOpen: isNavbarOpen,
    onOpen: onNavbarOpen,
    onClose: onNavbarClose,
  } = useDisclosure();
  const { data: session } = useSession();
  const {
    isLoggedIn,
    authenticate,
    logOut,
    showWidgetModal,
    // getPortfolio,
    // getSupportedTokens,
    // getWallets,
    // getUserDetails,
  } = useOkto() as OktoContextType;
  const idToken = useMemo(
    () =>
      session
        ? //@ts-expect-error id_token not in session types
          session?.id_token
        : null,
    [session]
  );

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
  useEffect(() => {
    if (session && !isLoggedIn) {
      handleAuthenticate();

      // fetchWallets();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [session, isLoggedIn]);

  // async function fetchWallets() {
  //   try {
  //     const supportedNetworks = await createWallet();

  //     // await getSupportedNetworks();
  //     console.log("Supported networks:", supportedNetworks);
  //   } catch (error) {
  //     console.error("Error fetching supported networks:", error);
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
    disconnect();
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
          <Button onClick={async () => showWidgetModal()}>create wallet</Button>
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
                      onClick={() => handleLogout()}
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
                    isLoading={isLoading}
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
                          <Button
                            variant={"outline"}
                            leftIcon={<FaGoogle />}
                            onClick={() => handleLogin()}
                          >
                            Continue with Google
                          </Button>
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
