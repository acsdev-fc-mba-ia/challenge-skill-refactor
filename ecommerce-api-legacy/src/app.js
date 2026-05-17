const express = require('express');
const config = require('./config');
const { getDb } = require('./database');
const checkoutRoutes = require('./routes/checkoutRoutes');
const reportRoutes = require('./routes/reportRoutes');
const userRoutes = require('./routes/userRoutes');
const errorHandler = require('./middleware/errorHandler');

const app = express();
app.use(express.json());

getDb(); // initialize schema and seed data

app.use('/api', checkoutRoutes);
app.use('/api', reportRoutes);
app.use('/api', userRoutes);
app.use(errorHandler);

app.listen(config.port, () => {
    console.log(`Frankenstein LMS rodando na porta ${config.port}...`);
});
