require('dotenv').config();

if (!process.env.PAYMENT_KEY && process.env.NODE_ENV === 'production') {
    throw new Error('PAYMENT_KEY must be set in production');
}

module.exports = {
    port: parseInt(process.env.PORT || '3000', 10),
    dbPath: process.env.DB_PATH || ':memory:',
    paymentGatewayKey: process.env.PAYMENT_KEY || 'replace-me',
    smtpUser: process.env.SMTP_USER || '',
    nodeEnv: process.env.NODE_ENV || 'development',
};
