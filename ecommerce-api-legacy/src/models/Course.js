const { getDb } = require('../database');

class Course {
    static findActiveById(id) {
        return getDb()
            .prepare('SELECT * FROM courses WHERE id = ? AND active = 1')
            .get(id);
    }
}

module.exports = Course;
