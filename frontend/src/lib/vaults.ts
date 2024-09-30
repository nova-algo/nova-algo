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

export const vaults: Vault[] = [
  {
    id: "1",
    name: "Alpha Vault",
    description: "High-risk, high-reward Advanced strategy",
    performance: "+25% YTD",
    avatar: "/images/drift.webp",
    risk: "**Market Risk**\n\nAlpha Vault is exposed to market risk as it takes directional positions based on supply and demand zones. If the market moves against the predicted direction, the strategy may incur losses. Sudden market shifts or unexpected events can invalidate the identified zones, leading to potential losses.\n\n**Liquidity Risk**\n\nThe strategy relies on the liquidity available on the Drift protocol to execute its trades. If there is insufficient liquidity at the desired price levels, the strategy may face difficulties in entering or exiting positions, potentially impacting its profitability. Low liquidity can also result in slippage, where the actual execution price differs from the intended price.\n\n**Technical Risk**\n\nAs the strategy is implemented using code and interacts with the Drift protocol, it is subject to technical risks such as software bugs, vulnerabilities, or failures in the underlying blockchain infrastructure. Any issues or disruptions in the code or the Drift protocol could lead to unexpected behavior or losses for the strategy.",
    strategy:
      "Alpha Vault employs a supply and demand zone trading strategy on the Drift protocol, primarily focused on SOL perpetual swaps. The strategy aims to identify key supply and demand zones based on historical price data and places limit orders at these levels to capture potential price reversals. The strategy also incorporates a kill switch mechanism to close positions when certain profit or loss thresholds are met.\n\n**The strategy is built on the Drift protocol, which is a decentralized perpetual swap exchange on the Solana blockchain. Funds are stored in a non-custodial wallet, meaning they cannot be withdrawn by anyone but you.**",
    depositTokens: [
      {
        name: "USDC",
        image: "/icons/usdc.svg",
      },
    ],
    tradingTokens: [
      {
        name: "SOL",
        image: "/icons/sol.svg",
      },

      {
        name: "JUP",
        image: "/icons/jup.svg",
      },
    ],
    apy: "41.24%",
    tvl: "$25.9M",
    capacity: "86.48%",
  },
  {
    id: "2",
    name: "Beta Vault",
    description: "Balanced approach for steady growth",
    performance: "+15% YTD",
    avatar: "/images/bonk.webp",
    risk: "**Market Risk**\n\nBeta Vault is exposed to market risk as it takes directional positions based on technical indicators. If the market moves against the predicted direction, the strategy may incur losses. Sudden market shifts or unexpected events can invalidate the signals generated by the Bollinger Bands and EMA, leading to potential losses.\n\n **Liquidity Risk**\n\nThe strategy relies on the liquidity available on the Drift protocol to execute its trades. If there is insufficient liquidity at the desired price levels, the strategy may face difficulties in entering or exiting positions, potentially impacting its profitability. Low liquidity can also result in slippage, where the actual execution price differs from the intended price.\n\n **Technical Risk**\n\nAs the strategy is implemented using code and interacts with the Drift protocol, it is subject to technical risks such as software bugs, vulnerabilities, or failures in the underlying blockchain infrastructure. Any issues or disruptions in the code or the Drift protocol could lead to unexpected behavior or losses for the strategy.",
    strategy:
      "Beta Vault employs a Bollinger Bands and Exponential Moving Average (EMA) crossover strategy on the Drift protocol, primarily focused on the 1MBONK perpetual swap. The strategy aims to identify potential entry and exit points based on the relationship between the price, Bollinger Bands, and EMA. It enters a long position when the price closes above the upper Bollinger Band or when the EMA crosses above the price. The strategy also incorporates a kill switch mechanism to close positions when the price falls below the EMA.\n\n**The strategy is built on the Drift protocol, which is a decentralized perpetual swap exchange on the Solana blockchain. Funds are stored in a non-custodial wallet, meaning they cannot be withdrawn by anyone but you.**",
    depositTokens: [
      {
        name: "USDC",
        image: "/icons/usdc.svg",
      },
    ],
    tradingTokens: [
      {
        name: "SOL",
        image: "/icons/sol.svg",
      },
    ],
    apy: "32.40%",
    tvl: "$15.2M",
    capacity: "73.21%",
  },
  {
    id: "3",
    name: "Gamma Vault",
    description: "Conservative strategy for capital preservation",
    performance: "+8% YTD",
    avatar: "/icons/boost.svg",
    risk: "**Funding Rate Volatility Risk**\n\nGamma Vault is exposed to funding rate volatility risk. Rapid and large movements in the funding rate can impact the strategy's ability to enter or exit positions at desired levels. High funding rate volatility can lead to unexpected position entries or exits, potentially reducing the strategy's profitability.\n\n **Counterparty Risk**\n\nGamma Vault faces counterparty risk when trading on Drift protocol. If the protocol experiences issues, such as liquidity problems, technical glitches, or smart contract vulnerabilities, the vault's positions and funds may be at risk. The strategy relies on the stability and reliability of Drift protocol for executing trades and managing positions.",
    strategy:
      "Gamma Vault employs a funding rate-based trading strategy on Drift protocol's perpetual swaps. The strategy takes long positions when the funding rate drops below a certain negative threshold (-43 bps) and enters short positions when the funding rate exceeds a positive threshold (32 bps). Positions are managed with predefined take-profit and stop-loss levels. \n\n**The strategy is built on a smart contract, meaning funds cannot be withdrawn by anyone but you.**",
    depositTokens: [
      {
        name: "JITOSOL",
        image: "/icons/jitosol.svg",
      },
    ],
    tradingTokens: [
      {
        name: "JITOSOL",
        image: "/icons/jitosol.svg",
      },
    ],
    apy: "21.33%",
    tvl: "$10.3M",
    capacity: "46.53%",
  },
];
