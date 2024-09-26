import { Box, useColorModeValue } from "@chakra-ui/react";
import Hero from "./Hero";
import Featured from "./Featured";
import Footer from "../Footer";
import Testimonials from "./Testimonials";
import Header from "../Header";

export default function Homepage() {
  const bgColor = useColorModeValue("gray.50", "gray.900");
  //   const textColor = useColorModeValue("gray.800", "gray.100");

  return (
    <Box bg={bgColor} minH="100vh" position="relative" overflow="hidden">
      <Header />
      <Hero />
      <Featured />
      <Testimonials />
      <Footer />
    </Box>
  );
}
