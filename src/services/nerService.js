import axios from "axios";
import dotenv from "dotenv";
dotenv.config();

const TOGETHER_API_URL = "https://api.together.xyz/inference";
const NIFTY_50_TICKERS = [
    'ADANIENT.NS', 'ADANIPORTS.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AXISBANK.NS', 
    'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BPCL.NS', 'BHARTIARTL.NS', 
    'BRITANNIA.NS', 'CIPLA.NS', 'COALINDIA.NS', 'DIVISLAB.NS', 'DRREDDY.NS', 
    'EICHERMOT.NS', 'GRASIM.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS', 
    'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'ITC.NS', 
    'INDUSINDBK.NS', 'INFY.NS', 'JSWSTEEL.NS', 'KOTAKBANK.NS', 'LTIM.NS', 'LT.NS', 
    'M&M.NS', 'MARUTI.NS', 'NTPC.NS', 'NESTLEIND.NS', 'ONGC.NS', 'POWERGRID.NS', 
    'RELIANCE.NS', 'SBILIFE.NS', 'SHRIRAMFIN.NS', 'SBIN.NS', 'SUNPHARMA.NS', 'TCS.NS', 
    'TATACONSUM.NS', 'TATAMOTORS.NS', 'TATASTEEL.NS', 'TECHM.NS', 'TITAN.NS', 
    'ULTRACEMCO.NS', 'WIPRO.NS'
];

const extractEntities = async (prompt) => {
    // Corrected prompt template
    const system_prompt = `[INST]
You are an expert financial entity extractor for the Indian stock market, specifically for Nifty 50 stocks.
Your task is to extract three entities from the user's text: company_name, ticker, and date_range.

You MUST adhere to these rules:
1.  **Ticker Format:** The ticker MUST end with ".NS" and be from the provided list of valid Nifty 50 tickers.
2.  **Resolve Ambiguity:** If a company name is ambiguous (e.g., "Tata"), use the context in the text to find the correct ticker from the list.
3.  **Missing Entities:** If any entity cannot be found, its value MUST be null.
4.  **Output Format:** You MUST return ONLY a single, valid JSON object. Do not include any explanations, apologies, or text outside the JSON.

Here is the list of valid Nifty 50 tickers:
${NIFTY_50_TICKERS.join(', ')}

--- EXAMPLES ---

Text: "What do you think about reliance industries for next month?"
[/INST]
{
  "company_name": "Reliance Industries",
  "ticker": "RELIANCE.NS",
  "date_range": "next month"
}
[INST]
Text: "show me tata motors prediction for 15 days"
[/INST]
{
  "company_name": "Tata Motors",
  "ticker": "TATAMOTORS.NS",
  "date_range": "15 days"
}
[INST]
Text: "what is the general market trend"
[/INST]
{
  "company_name": null,
  "ticker": null,
  "date_range": null
}
[INST]
Text: "${prompt}"
[/INST]`;

    try {
        const response = await axios.post(
            TOGETHER_API_URL,
            {
                model: 'mistralai/Mixtral-8x7B-Instruct-v0.1',
                prompt: system_prompt,
                max_tokens: 100,
                temperature: 0.1,
                stop: ["[/INST]", "```"] 

            },
            {
                headers: {
                    Authorization: `Bearer ${process.env.TOGETHER_API_KEY}`,
                    "Content-Type": "application/json",
                },
            }
        );

        const rawOutput = response.data.choices?.[0]?.text?.trim() || "{}";
        let extractedData;
        try {
            // **FIX: Robustly extract the JSON object from the raw output**
            const startIndex = rawOutput.indexOf('{');
            const endIndex = rawOutput.lastIndexOf('}');
            
            if (startIndex !== -1 && endIndex !== -1 && endIndex > startIndex) {
                const jsonString = rawOutput.substring(startIndex, endIndex + 1);
                extractedData = JSON.parse(jsonString);
            } else {
                throw new Error("No valid JSON object found in LLM output.");
            }
        } catch (e) {
            console.error("JSON Parse Error:", e, "Raw Output:", rawOutput);
            extractedData = { company_name: null, ticker: null, date_range: null };
        }
        return extractedData;
    } catch (error) {
        console.error("NER Service Error:", error.response?.data || error.message);
        return { company_name: null, ticker: null, date_range: null };
    }
};

export { extractEntities };