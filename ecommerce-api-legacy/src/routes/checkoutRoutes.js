const { Router } = require('express');
const checkoutController = require('../controllers/checkoutController');

const router = Router();
router.post('/checkout', checkoutController.process);

module.exports = router;
