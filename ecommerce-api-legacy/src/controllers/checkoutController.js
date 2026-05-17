const checkoutService = require('../services/checkoutService');

exports.process = (req, res, next) => {
    try {
        const { usr: username, eml: email, pwd: password, c_id: courseId, card: creditCard } = req.body;

        if (!username || !email || !courseId || !creditCard) {
            return res.status(400).json({ error: 'Bad Request' });
        }

        const result = checkoutService.processCheckout({ username, email, password, courseId, creditCard });
        res.status(200).json(result);
    } catch (err) {
        next(err);
    }
};
