import Header from "@/components/Header";
import MarkdownRenderer from "@/components/MarkdownRenderer";
import { Box } from "@chakra-ui/react";

export default function Faq() {
  return (
    <>
      <Header />
      <Box mt={12}>
        <MarkdownRenderer
          markdown="# Frequently Asked Questions

## General Questions

### What is a vault investment?
A vault investment is a pooled investment strategy where funds from multiple investors are combined and managed according to a specific strategy.

### How do I get started?
Create an account, verify your identity, fund your account, and choose a vault to invest in.

### Is there a minimum investment amount?
Minimum investments vary by vault. Check each vault's details for specific requirements.

## Account Management

### How do I fund my account?
You can fund your account through your cryptocurrency wallet.

### Can I invest in multiple vaults?
Yes, you can diversify your investments across multiple vaults.

### How do I track my investments?
Use our dashboard to monitor real-time performance, analytics, and projections for your investments.

## Investments and Returns

### How are returns calculated?
Returns are calculated based on the performance of the assets in each vault, minus any fees.

### Are my returns guaranteed?
No investment returns are guaranteed. All investments carry risk.

### How often are returns distributed?
Distribution schedules vary by vault. Some distribute returns monthly, others quarterly or annually.

## Withdrawals and Fees

### How do I withdraw my funds?
Request a withdrawal through your account dashboard. Processing times may vary.

### Are there fees for withdrawals?
Some vaults may have withdrawal fees or lock-up periods. Check each vault's terms.

### What fees do you charge?
We charge management fees and performance fees, which vary by vault. All fees are transparently disclosed.

## Security and Compliance

### How do you protect my investments?
We use bank-level encryption, cold storage for digital assets, and regular security audits.

### Are you regulated?
Yes, we comply with all relevant financial regulations in our operating jurisdictions.

### How is my personal information protected?
We adhere to strict data protection policies and never share your information without consent.

## Support

### How can I contact customer support?
Reach out via in-app chat, email at support@novaalgo.com, or on X (Twitter) https://x.com/@novaalgo.

### Do you offer educational resources?
Yes, we provide a knowledge base, webinars, and blog posts to help you make informed decisions."
        />
      </Box>
    </>
  );
}
