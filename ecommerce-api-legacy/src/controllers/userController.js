const User = require('../models/User');

exports.deleteUser = (req, res, next) => {
    try {
        User.deleteById(req.params.id);
        res.json({ msg: 'Usuário deletado' });
    } catch (err) {
        next(err);
    }
};
