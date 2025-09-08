import { Router } from "express";
import {Userquery} from '../controllers/queryController.js';


const router = Router();

router.route('/prompt').post(Userquery);

export default router;