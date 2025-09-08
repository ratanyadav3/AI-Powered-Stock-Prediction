import express from 'express';
import cookieParser from 'cookie-parser';
import cors from 'cors';

const app = express();


app.use(cors({
    origin: process.env.CORS_ORIGIN,
    credentials: true
}))



app.use(express.json({limit: "16kb"}))
app.use(cookieParser());
app.use(express.urlencoded({extended:true,limit:"16kb"}));

app.get("/api/v1/health",(req,res)=>{
    res.json({ status: "OK", message: "Server is running" });
})

import queryRoutes from './routes/queryRoutes.js';

app.use("/api/v1/query",queryRoutes);

export {app};