module.exports = (err, req, res, next) => {
    const status = err.status || 500;
    const message = err.message || 'Internal Server Error';
    if (status >= 500) {
        console.error(`[ERROR] ${req.method} ${req.path}:`, err);
    }
    res.status(status).json({ error: message });
};
