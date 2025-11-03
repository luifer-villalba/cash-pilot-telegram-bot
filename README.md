# CashPilot Telegram Bot 🤖

Telegram bot client for pharmacy cash register reconciliation. Connects to CashPilot backend API.

## 🚀 Quickstart

### Prerequisites
- Python 3.12+
- Telegram Bot Token (from @BotFather)

### Setup

1. **Clone and enter directory**
```bash
git clone https://github.com/luifer-villalba/cash-pilot-telegram-bot.git
cd cash-pilot-telegram-bot
```

2. **Create environment file**
```bash
cp .env.example .env
# Edit .env with your TELEGRAM_TOKEN and CASHPILOT_API_URL
```

3. **Install dependencies**
```bash
make install
```

4. **Run bot**
```bash
make run
```

## 🛠️ Commands

| Command | Description |
|---------|-------------|
| `make install` | Install dependencies |
| `make fmt` | Auto-format code |
| `make lint` | Check code quality |
| `make test` | Run tests |
| `make run` | Start bot |

## 📁 Project Structure
```
cash-pilot-telegram-bot/
├── src/
│   ├── telegram_main.py    # Bot entrypoint
│   └── telegram_bot/       # Bot logic (TBD)
├── tests/                  # Test suite
├── requirements.txt        # Dependencies
├── pyproject.toml         # Tool configs
├── .env.example           # Environment template
├── .gitignore
├── Makefile
└── README.md
```

## 📖 License

MIT
