import { Button, Image } from "@chakra-ui/react";

export default function ConnectButton({
  title,
  icon,
  callback,
}: {
  title: string;
  icon: string;
  callback: () => void;
}) {
  return (
    <Button
      onClick={callback}
      leftIcon={<Image src={icon} w={"48px"} alt="ICON" />}
    >
      {title || "Connect"}
    </Button>
  );
}
