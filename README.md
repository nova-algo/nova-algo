# Nova Algo x Radar Hackathon

<!-- Video Demo - [Demo video](https://www.loom.com/share/38af2c5c8a8e46c29e16e316099dcee1) <br />
Live Link - [Enigma-Protocol dapp](https://enigma-protocol.vercel.app/) <br />
Pitch Deck - [Figma slides](https://www.figma.com/proto/diEzJsJcpkEzwZfWfRqULh/Enigma-Protocol?node-id=1-205&t=PWgmft5uE7HVKyqy-1&scaling=contain&content-scaling=fixed&page-id=0%3A1) <br/> -->

## ✨ Description

[Nova Algo](https://enigma-protocol.vercel.app/) is an algorithmic trading protocol for solana. It brings professional-grade quant finance trading algorithms and tools to retail on Solana. It trades on the Drift protocol DEX. We employed active yield vaults where users can pool in their USDC, BONK into the vault pools, and earn real yield from our algorithmic strategies which are connected to these vaults and running 24/7 under close monitoring.

## Inspiration
97% of traders are not profitable, the market is so efficient that the only way you can be profitable is if you find your edge, that's why all the hedge funds and wall street employ quantitative methods so they can beat the market and they are so secretive about their alpha. We thought about coming up with our own edge with automation and coming up with quantitative methods to build strategies that would otherwise have been impossible to implement without automation to build out our edge and then allow retail to enjoy the profits from the institutional quantitative trading methods from our platform.

## What it does
Nova Algo enables Drift Protocol based investment vaults that trade on Solana using custom made algorithmic trading strategies.

We deployed our strategies using Drift Protocols vaults, allowing our strategies to be investable to any DeFi user with a profit-sharing fee model.

The DeFi user can invest in the strategies on our vaults using a familiar yield farming user interface directly from their wallet depositing USDC or BONK.


## How we built it

We wrote our trading strategies using `Python` and backtested them with the `Backtesting.py` library with some historical data. We also used trading and data analysis libraries like `pandas-ta`, `pandas` etc.

We wrote our bots then connected it to our Drift protocol based vaults that trade on the Drift Protocol DEX. We are currently running three different strategies on our vaults at the moment: 

1. The Drifting Tiger Vault - which trades the supply and demand zone strategy which trades the SOL-USD perpetual pair. Users deposit USDC into this vault.

2. The Bonking Dragon Vault - which trades the bollinger band + EMA strategy for the 1MBONK perpetual pair. Users deposit can deposit BONK or USDC into this vault. If users deposit BONK into the vault our bot borrows USDC on their behalf and trades with it, in a bull market they earn as their BONK appreciates in value and earn from from the vault's profits as well.

3. The Double Boost Vault - which trades a funding rate based strategy on any pair we input, this strategy is very flexible as we can aim to improve it to even perform funding rate arbitrage between different pairs funding rates. Users deposit USDC into this vault.

## Where we deployed to/contract details

We created and deployed our different vaults on the Solana Devnet Chain.

1. Drifting Tiger Vault - HrAuKuC8KuhqRcdmUu3WhSrNFv4HaV6XtqCdashhVH1A

2. Bonking Dragon - 5QAPFbeAHtgb8LkbDBMSyaAmwtQRufWceQLLaxdSse6M

3. Double Boost - 4K1s2DtLXrYXVMYShDdLLWTLezpyTBKpTFz2DEpt8QkF

## Installation

To install this project:

### Prerequisites

<!-- - [Git](https://git-scm.com/downloads) -->
- [Python](https://www.python.org/downloads/) (version 3.10 or higher)
- [pyenv](https://github.com/pyenv/pyenv#installation)
- [Poetry](https://python-poetry.org/docs/#installation)

### Steps

1. **Clone the Repository**

   Clone the project repository from GitHub:

   ```
   git clone https://github.com/nova-algo/nova-algo
   ```

2. **Navigate to the Project Directory**

   Change into the project directory:

   ```
   cd nova_algo/backend
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

7. **Run the Strategy**

   You can run the strategy using the main script:

   ```
   python main.py
   ```

8. **Configure the Vault (Optional)**

   If you need to configure or initialize a vault, you can use the `configure_vault.py` or `initialize_vault.py` scripts:

   ```
   python src/vault/configure_vault.py --help
   python src/vault/initialize_vault.py --help
   ```

   Follow the prompts or provide the necessary arguments to configure or initialize a vault.

9. **Environment Variables**

   Make sure to set up your environment variables. Create a `.env` file in the `backend` directory with the necessary configurations.

10. **Additional Notes**

    - The project uses various libraries such as `anchorpy`, `solana`, `driftpy`, and others. Make sure you're familiar with their documentation.
    - The `src/api/drift/api.py` file contains the main DriftAPI implementation.
    - The `src/strategy/bollingerbands.py` file contains the Bollinger Bands strategy implementation.
