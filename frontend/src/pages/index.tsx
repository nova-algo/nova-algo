import { AnimatedSVG } from "@/components/AnimatedLogo";
import Homepage from "@/components/Homepage";
import { Box } from "@chakra-ui/react";
import { useEffect, useState } from "react";

export default function Home() {
  const [isReady, setIsReady] = useState(false);
  useEffect(() => {
    setTimeout(() => {
      setIsReady(true);
    }, 2500);
  }, []);
  if (!isReady)
    return (
      <Box
        w={"100vw"}
        h={"100vh"}
        display={"flex"}
        justifyContent={"center"}
        alignItems={"center"}
      >
        <AnimatedSVG />
      </Box>
    );
  return <Homepage />;
}
