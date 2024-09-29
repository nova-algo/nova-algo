import { Link } from "@chakra-ui/next-js";
import { HStack, StackDirection, useBreakpointValue } from "@chakra-ui/react";

export default function Navbar() {
  const dir = useBreakpointValue({
    base: "column",
    md: "row",
  }) as StackDirection;
  const color = useBreakpointValue({
    base: "black",
    md: "white",
  });
  const NavLinks = () => (
    <HStack as={"nav"} gap={5} fontWeight={500} flexDir={dir} color={color}>
      <Link href={"/vaults"} _hover={{ color: "blue.300" }}>
        Vaults
      </Link>
      <Link href={"/how-it-works"} _hover={{ color: "blue.300" }}>
        How it works
      </Link>
      <Link href={"/faqs"} _hover={{ color: "blue.300" }}>
        FAQs
      </Link>
    </HStack>
  );
  return <NavLinks />;
}
