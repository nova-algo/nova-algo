import { Link } from "@chakra-ui/next-js";
import {
  Box,
  Button,
  HStack,
  Image,
  useColorModeValue,
} from "@chakra-ui/react";

export default function Header() {
  const bgColor = useColorModeValue("white", "gray.900");
  return (
    <Box p={5} pos={"fixed"} top={0} width={"full"} zIndex={1000}>
      <HStack
        bg={bgColor}
        rounded={"full"}
        px={{ base: 3, md: 4 }}
        py={{ base: 2, md: 3 }}
        justify={"space-between"}
      >
        <Box>
          <Image src="/transparent-app-logo.png" alt="Nova Algo logo" />
        </Box>
        <HStack as={"nav"}>
          <Link href={"#"}>Vaults</Link>
          <Link href={"#"}>How it works</Link>
          <Link href={"#"}>FAQs</Link>
        </HStack>
        <Box>
          <Button>Try Nova Algo Free</Button>
        </Box>
      </HStack>
    </Box>
  );
}
