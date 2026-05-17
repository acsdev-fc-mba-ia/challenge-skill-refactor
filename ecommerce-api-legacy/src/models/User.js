const { getDb } = require('../database');

class User {
    static findByEmail(email) {
        return getDb().prepare('SELECT * FROM users WHERE email = ?').get(email);
    }

    static create({ name, email, hashedPassword }) {
        const result = getDb()
            .prepare('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)')
            .run(name, email, hashedPassword);
        return result.lastInsertRowid;
    }

    static deleteById(id) {
        getDb().prepare('DELETE FROM users WHERE id = ?').run(id);
    }
}

module.exports = User;
