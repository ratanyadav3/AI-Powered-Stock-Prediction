import mongoose from "mongoose";

const connectDB = async()=>{

    try {
        const connectionInstance = await mongoose.connect(`${process.env.MONGODB_URI}`);
        console.log(`DataBase Connected DB HOST !! ${connectionInstance.connection.host}`);
    } catch (error) {
        console.log('DataBase Connection Failed ',error);
        process.exit(1);
    }
}

export default connectDB;


// export default connectDB;