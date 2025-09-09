import axios from "axios";
import dotenv from "dotenv";
dotenv.config();

const TOGETHER_API_URL = "https://api.together.xyz/inference";

const extractEntities = async (prompt) => {

  try {
    const response = await axios.post(
      TOGETHER_API_URL,
      {
        model: 'mistralai/Mixtral-8x7B-Instruct-v0.1',
        prompt: `
          Extract entities from the following text:
          Text: "${prompt}"
          Return ONLY valid JSON with keys: company_name, ticker, date_range.
          No explanation, no extra text, no newlines
        `,
        max_tokens: 100,
        temperature: 0.1,
      },
      {
        headers: {
          Authorization: `Bearer ${process.env.TOGETHER_API_KEY}`,
          "Content-Type": "application/json",
        },
      }
    );

    const rawOutput =
      response.data.choices?.[0]?.text?.trim() || "{}";
    let extractedData;
    try {
     extractedData = JSON.parse(rawOutput);
    } catch (e) {
    console.error("JSON Parse Error:", e);
    extractedData = { company_name: null, ticker: null, date_range: null };
    }
    return extractedData;
} catch (error) {
    console.error("NER Service Error:", error.response?.data || error.message);
    return { company_name: null, ticker: null, date_range: null };
  }
};

export { extractEntities };
