import { Chat, Message } from "@/types";

export const sampleChats: Chat[] = [
  {
    id: "8f7d3b2e-1a4c-4d5b-9e6f-2c8d7b3a5f9e",
    title: "DeFi Trading Strategy",
    lastMessage: "Let's analyze the liquidity pools for better swap rates.",
    timestamp: new Date("2025-03-15T10:30:00Z"),
  },
  {
    id: "a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d",
    title: "NFT Market Analysis",
    lastMessage: "The floor price is showing an upward trend.",
    timestamp: new Date("2025-03-15T09:15:00Z"),
  },
  {
    id: "c4d5e6f7-8a9b-4c5d-6e7f-83e189d3a4b5",
    title: "Smart Contract Review",
    lastMessage:
      "I've checked the trading contract for potential vulnerabilities.",
    timestamp: new Date("2025-02-14T16:45:00Z"),
  },
  {
    id: "b5c6d7e8-9f0a-4b5c-7d8e-9f0a1b2c3d4e",
    title: "Gas Optimization",
    lastMessage: "Here's how we can reduce gas fees for your trades.",
    timestamp: new Date("2025-02-14T14:20:00Z"),
  },
];

export const sampleMessages: Message[] = [
  {
    text: "Can you help me analyze the liquidity pools for better swap rates?",
    sender: "user",
    timestamp: new Date("2025-03-15T10:29:00Z"),
    chatId: "8f7d3b2e-1a4c-4d5b-9e6f-2c8d7b3a5f9e",
  },
  {
    text: "Let's analyze the liquidity pools for better swap rates. I'll check Uniswap V3 pools first.\n\n**Key findings:**\n- Pool depth varies significantly across pairs\n- USDC/ETH pool shows highest liquidity\n- Consider using multiple hops for better rates\n\nWould you like me to analyze specific trading pairs?",
    sender: "ai",
    timestamp: new Date("2025-03-15T10:30:00Z"),
    chatId: "8f7d3b2e-1a4c-4d5b-9e6f-2c8d7b3a5f9e",
  },
  {
    text: "What's your analysis of the current NFT market trends?",
    sender: "user",
    timestamp: new Date("2025-03-15T09:14:00Z"),
    chatId: "a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d",
  },
  {
    text: "The floor price is showing an upward trend. Major collections have seen a 15% increase.\n\n**Market Analysis:**\n- Blue-chip collections up 15% this week\n- Trading volume increased by 23%\n- New unique wallets: +5,000\n\nThis suggests growing market confidence. Would you like specific collection data?",
    sender: "ai",
    timestamp: new Date("2025-03-15T09:15:00Z"),
    chatId: "a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d",
  },
  {
    text: "Could you review my trading smart contract for security issues?",
    sender: "user",
    timestamp: new Date("2025-02-14T16:44:00Z"),
    chatId: "c4d5e6f7-8a9b-4c5d-6e7f-83e189d3a4b5",
  },
  {
    text: "I've checked the trading contract for potential vulnerabilities. Found a few areas to improve.\n\n**Security Findings:**\n- Reentrancy guard missing in main function\n- Unchecked return values from external calls\n- Consider implementing pause mechanism\n\nShall we go through these issues in detail?",
    sender: "ai",
    timestamp: new Date("2025-02-14T16:45:00Z"),
    chatId: "c4d5e6f7-8a9b-4c5d-6e7f-83e189d3a4b5",
  },
  {
    text: "How can I optimize gas usage in my transactions?",
    sender: "user",
    timestamp: new Date("2025-02-14T14:19:00Z"),
    chatId: "b5c6d7e8-9f0a-4b5c-7d8e-9f0a1b2c3d4e",
  },
  {
    text: "Here's how we can reduce gas fees for your trades. We can batch transactions and use off-peak hours.\n\n**Optimization Strategies:**\n- Batch similar transactions together\n- Use off-peak hours (UTC 2-8AM)\n- Implement EIP-1559 fee structure\n\nWould you like to see some code examples?",
    sender: "ai",
    timestamp: new Date("2025-02-14T14:20:00Z"),
    chatId: "b5c6d7e8-9f0a-4b5c-7d8e-9f0a1b2c3d4e",
  },
];
