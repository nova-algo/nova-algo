import { Button, Stack } from "@chakra-ui/react";
import { ResponsiveModalSheet } from "./SheetOrModal";
import { Link } from "@chakra-ui/next-js";
import { useAppContext } from "@/context/app-context";
import { OktoContextType, useOkto } from "okto-sdk-react";
import { useSession, signOut } from "next-auth/react";

export default function LogoutPopup({
  isOpen,
  onClose,
}: {
  isOpen: boolean;
  onClose: () => void;
}) {
  const { appkitModal } = useAppContext();
  const { setAddress } = useAppContext();
  const { data: session } = useSession();
  const { isLoggedIn, logOut } = useOkto() as OktoContextType;

  async function handleLogout() {
    onClose();
    await appkitModal?.adapter?.connectionControllerClient
      ?.disconnect()
      .then(() => setAddress(""));

    session && (await signOut());
    isLoggedIn && logOut();
  }
  return (
    <>
      <ResponsiveModalSheet
        isOpen={isOpen}
        onClose={onClose}
        title="Welcome"
        content={
          <Stack spacing={3}>
            <Button as={Link} href={"/dashboard"}>
              Go to Dashboard
            </Button>
            <Button
              onClick={async () => {
                await handleLogout();
              }}
              colorScheme="red"
              variant={"outline"}
            >
              Logout
            </Button>
          </Stack>
        }
      />
    </>
  );
}
