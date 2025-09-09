// tests/nerService.test.js
import { extractEntities } from "../services/nerService.js";

const testPrompts = [
  "Predict Reliance stock price for next week",
  "Give short term analysis of TCS for the coming week",
  "What will be Infosys performance this week?",
  "Forecast HDFC Bank stock price for next 7 days",
  "Analyze Wipro movement for next few days",
  "Tell me ICICI Bank outlook for the coming week",
  "Predict Adani Enterprises trend in the next week",
  "Show me short term forecast of Tata Motors this week",
  "Estimate HCL Technologies price action over the next 5 days",
  "What will Infosys stock do by next Friday?"
];

describe("NER Service Tests (Short Term Prompts)", () => {
  testPrompts.forEach((prompt, index) => {
    test(`should extract entities from short term prompt ${index + 1}`, async () => {
      const entities = await extractEntities(prompt);

      console.log(`\nPrompt ${index + 1}:`, prompt);
      console.log("Extracted Entities:", entities);

      expect(entities).toHaveProperty("company_name");
      expect(entities).toHaveProperty("ticker");
      expect(entities).toHaveProperty("date_range");
    });
  });
});
