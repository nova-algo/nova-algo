import localFont from "next/font/local";

const geistSans = localFont({
  src: "../pages/fonts/GeistVF.woff",
  variable: "--font-geist-sans",
  weight: "100 900",
});

export const fonts = {
  geistSans,
  main: geistSans,
};
