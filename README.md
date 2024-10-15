# Nova Algo x Radar Hackathon

Video Demo - [Demo video](https://www.loom.com/share/8bdfc99d6cac49f9ae06746fe3b6fa8d) <br />
Live Link - [Nova Algo dapp](https://novaalgo.xyz/) <br />
Pitch Deck - [Figma slides](https://www.figma.com/proto/diEzJsJcpkEzwZfWfRqULh/Nova-Algo?node-id=1-102&t=5gDSMVrDudbXq7Zd-1&scaling=contain&content-scaling=fixed) <br/>

## ✨ Description

[Nova Algo](https://novaalgo.xyz/) is an algorithmic trading protocol for solana. It brings professional-grade quant finance trading algorithms and tools to retail on Solana. It trades on the Drift protocol DEX. We employed active yield vaults where users can pool in their USDC, SOL into the vault pools, and earn real yield from our algorithmic strategies which are connected to these vaults and running 24/7 under close monitoring.

## Inspiration
97% of traders are not profitable due to market efficiency. To succeed, one must find a unique edge. This is why hedge funds and Wall Street firms employ secretive quantitative methods to beat the market. We developed our own edge through automation and quantitative strategies that would be impossible to implement manually. Our platform will allow retail investors to benefit from institutional-grade quantitative trading methods.

## What it does
Nova Algo enables Drift Protocol based investment vaults that trade on Solana using custom made algorithmic trading strategies.

We deployed our strategies using Drift Protocol's vaults, allowing our strategies to be investable to any DeFi user with a profit-sharing fee model.

The DeFi user can invest in the strategies on our vaults using a familiar yield farming user interface directly from their wallet depositing USDC or SOL.


## How we built it

We wrote our trading strategies using `Python` and backtested them with the `Backtesting.py` library with some historical data. We also used trading and data analysis libraries like `pandas-ta`, `pandas` etc.

We wrote our bots then connected it to our Drift protocol based vaults that trade on the Drift Protocol DEX. We are currently running two different strategies on our vaults at the moment: 

1. The SOl Perp Real Yield Vault - is based on a LongShortTrend strategy that employs the Arnaud Legoux Moving Average (ALMA) to directionally trade longs and shorts for trending assets. It is a classic trend-based long/short strategy designed to beat or match buy-and-hold, while reducing the drawdowns. In future versions, dynamic position sizing and position accumulation will be introduced in order to increase the sharpe and substantially reduce the drawdowns.

2. The Gamma Market Maker Vault - it implements a Market Making strategy that employs the market quoting and market microstructure on SOLPERP to give an edge on the market while considering some key features like volatility, VWAP and Portfolio Management. It is designed to trade on the drift protocol and create a profitable edge as we offer both bid and ask on orderbook, while reducing the drawdowns

<!-- 3. The Drifting Tiger Vault - which trades the supply and demand zone strategy which trades the SOL-USD perpetual pair. Users deposit USDC into this vault. -->

## Where we deployed to/contract details

We created and deployed our different vaults on the Solana Devnet Chain.

1. Sol Perp Real Yield Vault - HrAuKuC8KuhqRcdmUu3WhSrNFv4HaV6XtqCdashhVH1A

2. Gamma Market Maker Vault - 5QAPFbeAHtgb8LkbDBMSyaAmwtQRufWceQLLaxdSse6M
<!-- 
3. Drifting Tiger Vault  - 4K1s2DtLXrYXVMYShDdLLWTLezpyTBKpTFz2DEpt8QkF -->

## Installation

To install this project:

### Prerequisites

<!-- - [Git](https://git-scm.com/downloads) -->
- [Python](https://www.python.org/downloads/) (version 3.10 or higher)
- [pyenv](https://github.com/pyenv/pyenv#installation)
- [Poetry](https://python-poetry.org/docs/#installation)
- [Solana CLI](https://docs.solanalabs.com/cli/install)
- Solana wallet with SOL:
  - For devnet: Use `solana airdrop 5` to get devnet SOL
  - For mainnet: Ensure you have real SOL in your wallet

### Steps

1. **Clone the Repository**

   Clone the project repository from GitHub:

   ```
   git clone https://github.com/nova-algo/nova-algo
   ```

2. **Navigate to the Project Directory**

   Change into the project directory:

   ```
   cd nova-algo/backend
   ```

3. **Set up Python Environment**

   Ensure you have the correct Python version installed using pyenv:

   ```
   pyenv install 3.10.11
   ```

   Then, you can either set the Python version globally:

   ```
   pyenv global 3.10.11
   ```

   Or, if you prefer to set the Python version only for this project, navigate to the project directory and run:

   ```
   pyenv local 3.10.11
   ```

   Using `pyenv local` is often preferred for project-specific Python version management as it doesn't affect your global Python environment.

   After setting up pyenv, ensure your IDE or text editor is using the correct Python interpreter:

   - For VS Code: Open the command palette (Ctrl+Shift+P), search for "Python: Select Interpreter", and choose the interpreter that matches your pyenv version (e.g., Python 3.10.11 64-bit ('nova_algo': pyenv)).
   - For PyCharm: Go to File > Settings > Project: nova_algo > Python Interpreter, and select the interpreter from your pyenv environment.

   You can verify the correct interpreter is being used by running:

   ```
   which python
   python --version
   ```

   These commands should show the path to your pyenv-managed Python and its version (3.10.11).

4. **Set up Poetry Environment**

   Create a new Poetry environment and use the Python version managed by pyenv:

   ```
   poetry env use $(pyenv which python)
   ```

5. **Install Dependencies**

   Install the project dependencies using Poetry:

   ```
   poetry install
   ```

6. **Activate the Poetry Environment**

   Activate the newly created Poetry environment:

   ```
   poetry shell
   ```

7. **Set up Environment Variables**

   Create a `.env` file in the `backend` directory based on the `.env.example` file:

   ```
   cp .env.example .env
   ```

   Edit the `.env` file and fill in your specific values for the environment variables.

8. **Deposit into Drift**

   To deposit SOL into Drift, run the deposit script:

   ```
   python src/api/drift/deposit.py
   ```

   This script will use the environment variables from your `.env` file to connect to the Drift protocol and make a deposit.

9. **Run the Strategy**

   You can run the strategy using the main script:

   ```
   python main.py
   ```

10. **Configure the Vault**

   If you need to configure or initialize a vault, you can use the `configure_vault.py` or `initialize_vault.py` scripts:

   ```
   python src/vault/configure_vault.py --help
   python src/vault/initialize_vault.py --help
   ```

   Follow the prompts or provide the necessary arguments to configure or initialize a vault.

11. **Environment Variables**

   Make sure to set up your environment variables. Create a `.env` file in the `backend` directory with the necessary configurations.

12. **Additional Notes**

    - The project uses various libraries such as `anchorpy`, `solana`, `driftpy`, and others. Make sure you're familiar with their documentation.
    - The `src/api/drift/api.py` file contains the main DriftAPI implementation.
    - The `src/strategy/trendfollowing.py` file contains the Trend Following strategy implementation.