import {
  Box,
  Button,
  Drawer,
  DrawerBody,
  DrawerCloseButton,
  DrawerContent,
  DrawerHeader,
  DrawerOverlay,
  Flex,
  HStack,
  Image,
  Link,
  useBreakpointValue,
  useDisclosure,
  VStack,
} from "@chakra-ui/react";
import { useRouter } from "next/router";
import { createElement, ReactNode } from "react";
import { IconType } from "react-icons";
import { BsChat } from "react-icons/bs";
import {
  LuHome,
  LuWallet,
  LuTrendingUp,
  LuSettings,
  LuMenu,
} from "react-icons/lu";

export default function DashboardWrapper({
  children,
}: {
  children: ReactNode;
}) {
  const isMobile = useBreakpointValue({ base: true, md: false });

  const { isOpen, onOpen, onClose } = useDisclosure();
  return (
    <Flex>
      {!isMobile && (
        <Box
          width="250px"
          bg="gray.100"
          p={4}
          height="100vh"
          pos={"sticky"}
          top={0}
        >
          <Image
            src="/images/desktop-logo-white.png"
            alt="app logo"
            maxW={"100px"}
            ml={3}
            mixBlendMode={"difference"}
            mb={5}
          />

          <DashboardNavbar />
        </Box>
      )}
      <Box flex={1}>
        <Box>
          <HStack
            bg="gray.100"
            height="50px"
            p={4}
            justify="space-between"
            pos={"sticky"}
            top={0}
            zIndex={10}
          >
            {isMobile && (
              <Button onClick={onOpen} leftIcon={<LuMenu />} variant="ghost">
                Menu
              </Button>
            )}
            <Link href="/">Back to site</Link>
          </HStack>
        </Box>
        {children}
      </Box>
      <Drawer isOpen={isOpen} placement="left" onClose={onClose}>
        <DrawerOverlay />
        <DrawerContent>
          <DrawerCloseButton />
          <DrawerHeader>Menu</DrawerHeader>
          <DrawerBody>
            <Sidebar />
          </DrawerBody>
        </DrawerContent>
      </Drawer>
    </Flex>
  );
}

export const DashboardNavbar = () => {
  return <Sidebar />;
};

const Sidebar = () => {
  return (
    <VStack spacing={4} align="stretch">
      <SidebarItem icon={LuHome} label="Dashboard" href="/dashboard" />
      <SidebarItem icon={LuWallet} label="Vaults" href="/dashboard/vaults" />
      <SidebarItem icon={BsChat} label="Chats" href="/dashboard/chats" />
      <SidebarItem
        icon={LuTrendingUp}
        label="Analytics"
        href="/dashboard/analytics"
      />

      <SidebarItem
        icon={LuSettings}
        label="Settings"
        href="/dashboard/settings"
      />
    </VStack>
  );
};

const SidebarItem = ({
  icon,
  label,
  href,
}: {
  icon: IconType;
  label: string;
  href: string;
  active?: boolean;
}) => {
  const router = useRouter();

  const pathname = router.pathname;

  const active = href === pathname?.toLowerCase();
  return (
    <Button
      leftIcon={createElement(icon)}
      justifyContent="flex-start"
      as={Link}
      variant="ghost"
      href={href}
      width="100%"
      _hover={{ bg: active ? "blue.600" : "blue.100" }}
      color={active ? "white" : undefined}
      bg={active ? "blue.500" : "transparent"}
    >
      {label}
    </Button>
  );
};
