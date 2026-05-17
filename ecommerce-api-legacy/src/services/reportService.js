const { getDb } = require('../database');
const { PaymentStatus } = require('../constants');

class ReportService {
    getFinancialReport() {
        const rows = getDb().prepare(`
            SELECT
                c.id     AS course_id,
                c.title  AS course_title,
                u.name   AS student_name,
                p.amount AS payment_amount,
                p.status AS payment_status
            FROM courses c
            LEFT JOIN enrollments e ON e.course_id = c.id
            LEFT JOIN users u       ON u.id = e.user_id
            LEFT JOIN payments p    ON p.enrollment_id = e.id
            ORDER BY c.id
        `).all();

        const reportMap = new Map();

        for (const row of rows) {
            if (!reportMap.has(row.course_id)) {
                reportMap.set(row.course_id, {
                    course: row.course_title,
                    revenue: 0,
                    students: [],
                });
            }

            const entry = reportMap.get(row.course_id);

            if (row.student_name) {
                if (row.payment_status === PaymentStatus.PAID) {
                    entry.revenue += row.payment_amount || 0;
                }
                entry.students.push({
                    student: row.student_name,
                    paid: row.payment_amount || 0,
                });
            }
        }

        return Array.from(reportMap.values());
    }
}

module.exports = new ReportService();
