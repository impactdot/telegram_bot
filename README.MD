# Telegram Alert Bot 🚀

## Overview

## Features

-   **Price Alerts**: Notifies users when the price of a selected cryptocurrency changes by a certain percentage.
-   **Volume Alerts**: Alerts users when the trading volume of a selected cryptocurrency changes significantly.
-   **News Alerts**: Sends the latest news articles related to the selected cryptocurrencies.
-   **Customizable**: Users can set custom time intervals and percentage thresholds for alerts.

## Installation

### Requirements

-   Python 3.8+
-   aiogram
-   requests

### Steps

1. Clone the repository:

    ```bash
    git clone https://github.com/yourusername/telegram_bot.git
    ```

2. Navigate to the project directory:

    ```bash
    cd telegram_bot
    ```

3. Install the required packages:

    ```bash
    pip install -r requirements.txt
    ```

4. Create a `.env` file and add your Telegram bot token:

    ```env
    TOKEN=your_token_here
    ```

5. Run the bot:

    ```bash
    python main.py
    ```

## Usage

1. Start the bot by sending `/start`.
2. Follow the instructions to select cryptocurrency pairs to track.
3. Use `/setinterval` to set the time interval for checking prices.
4. Use `/setpercentage` to set the percentage of change for alerts.
5. Use `/startalert` to start receiving alerts.
6. Use `/stopalert` to stop receiving alerts.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

[MIT](https://choosealicense.com/licenses/mit/)
