# Option Edge: Real-Time Options Contract Monitoring System

## Project Overview

Option Edge is a Python-based system designed to ingest live options tick data, build a comprehensive database of options contracts, and generate real-time alerts based on specific volume thresholds.

### Key Features

- **Live Tick Data Ingestion**: Captures real-time options market data
- **Dynamic Database Management**: Stores and updates options contract information
- **Automated Alert System**: Triggers notifications when contracts meet predefined volume criteria
- **Flexible Monitoring**: Customizable thresholds and tracking parameters
- **Custom Universe**: Contracts for single or multiple underlying symbols may be monitored


### Technologies Used
- Python
- Alpaca API
- WebSocket Protocols
- Time-series Database Management
- Real-time Data Processing
- Alerting Mechanisms

### Core Components
1. **Data Ingestion Module**
   - Connects to live market data feeds
   - Processes incoming tick data
   - Handles WebSocket/TCP-IP connections

2. **Database Management**
   - Stores options contract details
   - Tracks historical and real-time data
   - Efficient data storage and retrieval

3. **Alert Generation System**
   - Monitors contract volume thresholds
   - Sends customizable notifications
   - Supports multiple alert channels

## Setup and Installation

### Prerequisites
- Python 3.8+
- Required Libraries:
  ```
  pip install -r requirements.txt
  ```
- Alpaca market data subscription
  - Sign up for free to get API keys. 

## Data Information

The difference between free and paid data is as follows:

- **Free Data**: Includes indicative pricing, but values are delayed by 15 minutes.
- **Paid Data**: Grants access to real-time, consolidated BBO feed data.

Source: [Alpaca Historical Option Data Documentation](https://docs.alpaca.markets/docs/historical-option-data#:~:text=Indicative%20Pricing%20Feed%20is%20a,re%20delayed%20by%2015%20minutes.&text=OPRA%20is%20the%20consolidated%20BBO%20feed%20of%20OPRA.)


### Volume Thresholds
Easily adjust alert triggers by modifying threshold values:
- Single contract volume
- Aggregate volume across multiple contracts
- Time-based volume comparisons


## Performance Considerations
- Low-latency data processing
- Minimal system resource utilization
- Scalable architecture

## Roadmap
- [ ] Add machine learning predictive layer
- [ ] Expand alert customization options such as SMS, Slack, Telegram
- [ ] Implement more data visualization tools
- [ ] Add scripting for order entries and trade management


## License
Apache 2.0

## Disclaimer
This tool is for informational purposes only. Tick data is subject to change at any time due to corruption, incorrect trade information, and data provider outages. Not financial advice. Use responsibly.

---

**Contact**: tifanieoriley@gmail.com

