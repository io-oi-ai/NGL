NGL Crypto Analysis Bot

A Python-based cryptocurrency analysis bot that provides real-time market data analysis and investment advice.

🚀 Features

	•	💹 Supports queries by token name or contract address
	•	📊 Real-time market data analysis
	•	🤖 AI-driven investment advice
	•	📈 Multi-source data integration and analysis
	•	🔄 Real-time price monitoring
	•	⚡️ Rapid market response

🛠 Installation Steps

	1.	Clone the repository
python
pip install -r requirements.txt
	2.	Configure Environment Variables

	•	Copy .env.example to .env
	•	Fill in your API keys in the .env file:
 		TELEGRAM_BOT_TOKEN=Your Telegram Bot Token
		OPENAI_API_KEY=Your OpenAI API Key

3.	Run the Bot
python
python src/bot.py

User Guide

In Telegram:

	•	/start - Start using the bot
	•	/help - View help
	•	Send the token name directly (e.g., BTC)
	•	Send the token contract address

	2.	Configure Environment Variables

	•	Copy .env.example to .env
	•	Fill in your API keys in the .env file:

TELEGRAM_BOT_TOKEN=Your Telegram Bot Token
OPENAI_API_KEY=Your OpenAI API Key



	3.	Run the Bot
python
python src/bot.py

User Guide

In Telegram:

	•	/start - Start using the bot
	•	/help - View help
	•	Send the token name directly (e.g., BTC)
	•	Send the token contract address

Project Structure：
ngl/
├── src/
│   ├── bot.py # Main program
│   ├── services/ # Service layer
│   └── utils/ # Utility functions
├── .env # Environment variables (not committed)
├── .env.example # Environment variable template
└── requirements.txt # Project dependencies
Tech Stack

	•	Python 3.9+
	•	OpenAI GPT-4
	•	Telegram Bot API
	•	Web3 Library

Notes

	•	Do not share your API keys
	•	Regularly update dependencies
	•	Ensure proper logging and monitoring

Disclaimer

This project is for educational and research purposes only and does not constitute investment advice. The cryptocurrency market is highly risky; invest cautiously.

Contact

	•	Author: [Your Name]
	•	Email: [Your Email]

License

MIT License
