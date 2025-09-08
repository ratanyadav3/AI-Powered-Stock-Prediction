import { ApiError } from "../utils/ApiError.js";
import { ApiResponse } from "../utils/ApiResponse.js";
import { asyncHandler } from "../utils/asyncHandler.js";

const Userquery = asyncHandler(async (req, res) => {
    const data = req.body;

    if (!data || Object.keys(data).length === 0) {
        throw new ApiError(400, "Query body is required");
    }

    return res.status(201).json(
        new ApiResponse(201, "Just Checking my Incoming body", data)
    );
});

export { Userquery };
