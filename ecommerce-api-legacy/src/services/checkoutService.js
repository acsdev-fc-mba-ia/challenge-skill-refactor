const bcrypt = require('bcryptjs');
const { getDb } = require('../database');
const User = require('../models/User');
const Course = require('../models/Course');
const { PaymentStatus, CardBrand } = require('../constants');

class CheckoutService {
    processCheckout({ username, email, password, courseId, creditCard }) {
        const course = Course.findActiveById(courseId);
        if (!course) {
            const err = new Error('Curso não encontrado');
            err.status = 404;
            throw err;
        }

        let user = User.findByEmail(email);
        if (!user) {
            const hashedPassword = bcrypt.hashSync(password || '123456', 12);
            const userId = User.create({ name: username, email, hashedPassword });
            user = { id: userId };
        }

        const paymentStatus = creditCard.startsWith(CardBrand.VISA_PREFIX)
            ? PaymentStatus.PAID
            : PaymentStatus.DENIED;

        if (paymentStatus === PaymentStatus.DENIED) {
            const err = new Error('Pagamento recusado');
            err.status = 400;
            throw err;
        }

        const db = getDb();
        const { lastInsertRowid: enrollmentId } = db
            .prepare('INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)')
            .run(user.id, courseId);

        db.prepare('INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)')
            .run(enrollmentId, course.price, paymentStatus);

        db.prepare("INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))")
            .run(`Checkout curso ${courseId} por ${user.id}`);

        return { msg: 'Sucesso', enrollment_id: enrollmentId };
    }
}

module.exports = new CheckoutService();
