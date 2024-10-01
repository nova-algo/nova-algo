import { AnimatedSVG } from "@/components/AnimatedLogo";
import Homepage from "@/components/Homepage";
import { Box } from "@chakra-ui/react";
import Head from "next/head";
import { useEffect, useState } from "react";

export default function Home() {
  const [isReady, setIsReady] = useState(false);
  useEffect(() => {
    const tid = setTimeout(() => {
      setIsReady(true);
    }, 2500);
    return () => {
      tid && clearTimeout(tid);
    };
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
  return (
    <>
      <Head>
        <title>Nova Algo | Advanced Trading Vaults For Everyone</title>
        <meta
          name="description"
          content=" Nova Algo is an Advanced Trading App built for Everyone, Trade like a pro with Nova Algo"
        />
        <link rel="icon" href="/favicon.ico" />
      </Head>
      <Homepage />
    </>
  );
}
