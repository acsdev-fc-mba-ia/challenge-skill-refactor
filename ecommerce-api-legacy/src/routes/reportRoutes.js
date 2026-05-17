const { Router } = require('express');
const reportController = require('../controllers/reportController');

const router = Router();
router.get('/admin/financial-report', reportController.getFinancialReport);

module.exports = router;
