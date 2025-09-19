
import { ApiError } from "../utils/ApiError.js";
import { ApiResponse } from "../utils/ApiResponse.js";
import { asyncHandler } from "../utils/asyncHandler.js";
import { spawn } from "child_process";
import path from "path";

export const triggerDataCollection = asyncHandler(async (req, res) => {
    console.log("✅ Request reached triggerDataCollection controller");

    const runPythonScript = () => {
        return new Promise((resolve, reject) => {
            const scriptPath = path.resolve("ml_scripts", "daily_collector.py");
            console.log(`📂 Resolved Python script path: ${scriptPath}`);

            const pythonProcess = spawn("python3", [scriptPath]);

            let stdoutOutput = "";
            let stderrOutput = "";

            console.log("🐍 Python script started...");

            // Timeout (5 minutes)
            const timeout = setTimeout(() => {
                console.error("⏳ Python script timed out, killing process...");
                pythonProcess.kill();
                reject(
                    new ApiError(
                        500,
                        "Data collection script timed out after 5 minutes."
                    )
                );
            }, 300000);

            // STDOUT
            pythonProcess.stdout.on("data", (data) => {
                const msg = data.toString();
                console.log("📢 Python STDOUT:", msg.trim());
                stdoutOutput += msg;
            });

            // STDERR
            pythonProcess.stderr.on("data", (data) => {
                const errMsg = data.toString();
                console.error("⚠️ Python STDERR:", errMsg.trim());
                stderrOutput += errMsg;
            });

            // Process closed
            pythonProcess.on("close", (code) => {
                clearTimeout(timeout);
                console.log(`🚪 Python process closed with exit code: ${code}`);

                if (code !== 0) {
                    const errorMessage = `Data collection script failed with exit code ${code}. \nError: ${stderrOutput}`;
                    return reject(new ApiError(500, errorMessage));
                }

                if (stderrOutput) {
                    console.warn(
                        "⚠️ Python script produced warnings (stderr):",
                        stderrOutput
                    );
                }

                console.log("✅ Python script finished successfully.");
                resolve(stdoutOutput);
            });

            // Process error
            pythonProcess.on("error", (err) => {
                clearTimeout(timeout);
                console.error("❌ Failed to start Python script:", err.message);
                reject(
                    new ApiError(
                        500,
                        `Failed to start Python script: ${err.message}`
                    )
                );
            });
        });
    };

    console.log("➡️ Triggering Python script execution...");
    const scriptOutput = await runPythonScript();

    console.log("📦 Sending response back to client...");
    return res.status(200).json(
        new ApiResponse(
            200,
            { log: scriptOutput },
            "Data collection process finished successfully."
        )
    );
});
