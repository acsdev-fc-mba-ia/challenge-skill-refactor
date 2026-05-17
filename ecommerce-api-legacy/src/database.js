const Database = require('better-sqlite3');
const config = require('./config');

let db;

function getDb() {
    if (!db) {
        db = new Database(config.dbPath);
        initSchema();
    }
    return db;
}

function initSchema() {
    db.exec(`
        CREATE TABLE IF NOT EXISTS users (
            id    INTEGER PRIMARY KEY,
            name  TEXT,
            email TEXT,
            pass  TEXT
        );
        CREATE TABLE IF NOT EXISTS courses (
            id     INTEGER PRIMARY KEY,
            title  TEXT,
            price  REAL,
            active INTEGER
        );
        CREATE TABLE IF NOT EXISTS enrollments (
            id        INTEGER PRIMARY KEY,
            user_id   INTEGER,
            course_id INTEGER
        );
        CREATE TABLE IF NOT EXISTS payments (
            id            INTEGER PRIMARY KEY,
            enrollment_id INTEGER,
            amount        REAL,
            status        TEXT
        );
        CREATE TABLE IF NOT EXISTS audit_logs (
            id         INTEGER PRIMARY KEY,
            action     TEXT,
            created_at DATETIME
        );
    `);

    const { n } = db.prepare('SELECT COUNT(*) AS n FROM users').get();
    if (n === 0) {
        db.prepare("INSERT INTO users (name, email, pass) VALUES ('Leonan', 'leonan@fullcycle.com.br', '123')").run();
        db.prepare("INSERT INTO courses (title, price, active) VALUES ('Clean Architecture', 997.00, 1)").run();
        db.prepare("INSERT INTO courses (title, price, active) VALUES ('Docker', 497.00, 1)").run();
        db.prepare("INSERT INTO enrollments (user_id, course_id) VALUES (1, 1)").run();
        db.prepare("INSERT INTO payments (enrollment_id, amount, status) VALUES (1, 997.00, 'PAID')").run();
    }
}

module.exports = { getDb };
