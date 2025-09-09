# AI-Powered Stock Prediction

## Overview

**AI-Powered Stock Prediction** is an intelligent application designed to forecast short-term stock market trends. It currently performs **Named Entity Recognition (NER)** on user queries or prompts to extract relevant financial entities. Using these inputs, it forecasts short-term stock trends with an **LSTM model**.  

Future updates will include a **data collection layer** for historical and real-time market data, along with full integration of the frontend, backend, and deployment processes.

## Current Features

- **Query-Based NER**: Extracts company names, tickers, and date ranges from user prompts.  
- **Short-Term Stock Forecasting**: Uses an LSTM model to predict stock trends for extracted entities.  
- **Unit Testing**: Ensures reliability of NER and prediction modules with Jest tests.

## Future Roadmap

1. **Data Collection Layer** – Automatic retrieval of historical and real-time stock market data.  
2. **Data Processing Module** – Preprocessing and feature engineering for LSTM input.  
3. **LSTM Model Integration** – Enhanced short-term stock prediction.  
4. **Frontend Development** – User interface for queries, predictions, and visualizations.  
5. **Backend-Frontend Integration** – Connecting APIs with frontend for live predictions.  
6. **Testing & Deployment** – Unit, integration tests, and production deployment.

## Technologies Used

- **Node.js & Express.js**: Backend runtime and framework  
- **Jest**: Testing framework for unit and integration tests  
- **Together AI**: Provides NER capabilities for financial query processing  
- **LSTM (TensorFlow / Keras)**: Model for short-term stock trend prediction

## Installation

### Prerequisites

- Node.js (v14 or higher)  
- npm (v6 or higher)

### Steps

1. Clone the repository:

```bash
git clone https://github.com/ratanyadav3/AI-Powered-Stock-Prediction.git
cd AI-Powered-Stock-Prediction

npm install

npm run dev


# sample .env
PORT=3000
MONGODB_URI=mongodb://localhost:27017/stock_prediction
TOGETHER_API_KEY=your_together_ai_api_key_here

# Run tests
npm test
```

```mermaid
flowchart LR
    A[User Query] --> B[NER Extraction]
    B --> C[LSTM Prediction]
    C --> D[Result Display]
 ```

## Contribution

1. Contributions are welcome! Steps to contribute:

2. Fork the repository

3. Create a new branch (git checkout -b feature/YourFeature)

4. Make your changes

5. Commit your changes (git commit -am 'Add new feature')

6. Push to your branch (git push origin feature/YourFeature)

. Create a Pull Request to merge into main

## License

This project is licensed under the MIT License.