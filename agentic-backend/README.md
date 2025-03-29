# Rebalancr Backend

## Installation Guide

### Prerequisites
- [pyenv](https://github.com/pyenv/pyenv) for Python version management
- [Poetry](https://python-poetry.org/docs/) for dependency management

### Step 1: Install pyenv

#### macOS
```bash
# Using Homebrew
brew update
brew install pyenv
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zshrc
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zshrc
echo 'eval "$(pyenv init -)"' >> ~/.zshrc
source ~/.zshrc
```

#### Linux
```bash
curl https://pyenv.run | bash
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc
source ~/.bashrc
```

### Step 2: Set up Python using pyenv
```bash
# Install Python 3.10 (or your required version)
pyenv install 3.10.0

# Navigate to project directory
cd rebalancr/backend

# Set local Python version
pyenv local 3.10.0
```

### Step 3: Install Poetry
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

### Step 4: Install project dependencies
```bash
# Clone the repository (if you haven't already)
git clone https://github.com/yourusername/rebalancr.git
cd rebalancr/backend

# Install dependencies
poetry install
```

## Running the Server

```bash
# Activate the Poetry environment
poetry shell

# Start the FastAPI server
uvicorn rebalancr.api.app:app --reload --host 0.0.0.0 --port 8000
```

The server will be available at http://localhost:8000 with WebSocket endpoint at ws://localhost:8000/ws.
