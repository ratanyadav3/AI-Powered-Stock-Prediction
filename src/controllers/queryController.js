// import { ApiError } from "../utils/ApiError.js";
// import { ApiResponse } from "../utils/ApiResponse.js";
// import { asyncHandler } from "../utils/asyncHandler.js";
// import { extractEntities } from "../services/nerService.js";

// const Userquery = asyncHandler(async (req, res) => {
//     const data = req.body;
//     const prompt = data.Query;
//     if (!data || Object.keys(data).length === 0) {
//         throw new ApiError(400, "Query body is required");
//     }
//    const ExtractedData = await extractEntities(prompt);
//     return res.status(201).json(
//         new ApiResponse(201, "Just Checking my Incoming body", ExtractedData)
//     );
// });

// export { Userquery };



import { ApiError } from "../utils/ApiError.js";
import { ApiResponse } from "../utils/ApiResponse.js";
import { asyncHandler } from "../utils/asyncHandler.js";
import { extractEntities } from "../services/nerService.js";
import { spawn } from "child_process";
import path from "path";

const Userquery = asyncHandler(async (req, res) => {
    const { Query: prompt } = req.body;

    if (!prompt) {
        throw new ApiError(400, "The 'Query' field is required in the request body.");
    }

    // --- Step 1: Extract Entities using your NER Service ---
    const extractedData = await extractEntities(prompt);
    console.log("Extracted Data:", extractedData); 
    
    // We still validate both ticker and forecast_days are extracted successfully
    
    const { ticker, date_range } = extractedData;

    if (!ticker || !date_range) {
    throw new ApiError(400, "Could not extract a valid stock ticker and date range from the prompt.");
    }

    // --- Step 2: Call the Python Prediction Script ---
    const runPredictionScript = () => {
        return new Promise((resolve, reject) => {
            const scriptPath = path.resolve('ml_scripts', 'prediction_handler.py');
            
            // --- CHANGE: Only the ticker is now passed to the Python script ---
            const scriptArgs = [ticker]; 
            
            const pythonProcess = spawn('python3', [scriptPath, ...scriptArgs]);

            let jsonData = '';
            let errorData = '';

            pythonProcess.stdout.on('data', (data) => {
                jsonData += data.toString();
            });

            pythonProcess.stderr.on('data', (data) => {
                errorData += data.toString();
            });

            pythonProcess.on('close', (code) => {
                if (code !== 0) {
                    return reject(new ApiError(500, "Prediction script failed.", [errorData]));
                }
                try {
                    const parsedData = JSON.parse(jsonData);
                    resolve(parsedData);
                } catch (error) {
                    reject(new ApiError(500, "Failed to parse prediction script output.", [jsonData]));
                }
            });

            pythonProcess.on('error', (err) => {
                reject(new ApiError(500, `Failed to start Python script: ${err.message}`));
            });
        });
    };

    // --- Step 3: Await the result and send the response ---
    const predictionResult = await runPredictionScript();

    if (predictionResult.status === 'error') {
        throw new ApiError(500, "The prediction script returned an error.", [predictionResult.message]);
    }

    return res.status(200).json(
        new ApiResponse(200, predictionResult, "Prediction successful.")
    );
});

export { Userquery };