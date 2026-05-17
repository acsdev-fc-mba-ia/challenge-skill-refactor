const PaymentStatus = Object.freeze({
    PAID: 'PAID',
    DENIED: 'DENIED',
});

const CardBrand = Object.freeze({
    VISA_PREFIX: '4',
});

module.exports = { PaymentStatus, CardBrand };
