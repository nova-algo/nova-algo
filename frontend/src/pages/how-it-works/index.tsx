import Header from "@/components/Header";
import MarkdownRenderer from "@/components/MarkdownRenderer";
import { Box } from "@chakra-ui/react";

export default function HowItWorks() {
  return (
    <>
      <Header />
      <Box mt={12}>
        <MarkdownRenderer
          markdown="# How It Works

Welcome to our innovative vault investment platform. Here's a step-by-step guide to help you navigate and make the most of our services.

## 1. Create Your Account

Sign up quickly and easily. We'll need some basic information to get you started and ensure the security of your account.

## 2. Explore Available Vaults

Browse through our curated selection of investment vaults. Each vault has a unique strategy and risk profile.

## 3. Research and Compare

Dive deep into each vault's performance history, investment strategy, and risk metrics. Use our comparison tools to find the best fit for your goals.

## 4. Fund Your Account

Link your bank account or transfer crypto assets to fund your investment account. We support multiple currencies and cryptocurrencies.

## 5. Invest in Vaults

Choose your preferred vault(s) and allocate your funds. You can invest in multiple vaults to diversify your portfolio.

## 6. Monitor Performance

Track your investments in real-time through our intuitive dashboard. View detailed analytics, performance charts, and projected returns.

## 7. Adjust Your Strategy

As market conditions change or your goals evolve, easily rebalance your portfolio or switch between vaults.

## 8. Withdraw Funds

Request withdrawals at any time. Note that some vaults may have lock-up periods or withdrawal fees.

## 9. Stay Informed

Receive regular updates about your investments, market trends, and new vault opportunities through our newsletter and in-app notifications.

## 10. Get Support

Our dedicated support team is always ready to assist you with any questions or concerns. Reach out through in-app chat, email, or phone.

Start your investment journey today and take control of your financial future!"
        />
      </Box>
    </>
  );
}
