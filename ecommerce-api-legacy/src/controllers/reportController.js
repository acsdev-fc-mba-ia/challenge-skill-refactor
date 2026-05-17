const reportService = require('../services/reportService');

exports.getFinancialReport = (req, res, next) => {
    try {
        const report = reportService.getFinancialReport();
        res.json(report);
    } catch (err) {
        next(err);
    }
};
