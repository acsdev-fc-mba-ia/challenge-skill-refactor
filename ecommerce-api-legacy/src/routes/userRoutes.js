const { Router } = require('express');
const userController = require('../controllers/userController');

const router = Router();
router.delete('/users/:id', userController.deleteUser);

module.exports = router;
