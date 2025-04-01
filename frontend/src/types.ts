import { Session } from "next-auth";

export interface Message {
  text: string;
  sender: "user" | "ai";
  timestamp: Date;
  chatId?: string;
}

export interface Chat {
  id: string;
  title: string;
  lastMessage: string;
  timestamp: Date;
}
export interface Vault {
  id: string;
  name: string;
  description: string;
  performance: string;
  avatar: string;
  risk: string;
  strategy: string;
  depositTokens: {
    name: string;
    image: string;
  }[];
  tradingTokens: {
    name: string;
    image: string;
  }[];
  apy: string;
  tvl: string;
  capacity: string;
}
export type USER_ACCOUNT_TYPE = "WALLET" | "GOOGLE" | null;
export interface NextAuthSession extends Session {
  id_token?: string;
}
