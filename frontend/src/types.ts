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
