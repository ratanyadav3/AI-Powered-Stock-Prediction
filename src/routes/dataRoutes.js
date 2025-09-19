import { Router } from "express";
import {triggerDataCollection} from '../controllers/dataController.js';


const router = Router();

router.route('/collect').post(triggerDataCollection);

export default router;