const bcrypt = require('bcrypt');
const { Pool } = require('pg');

const pool = new Pool({
  host: process.env.DB_HOST || 'localhost',
  port: parseInt(process.env.DB_PORT || '5432'),
  database: process.env.DB_NAME || 'befreefitness',
  user: process.env.DB_USER || 'postgres',
  password: process.env.DB_PASSWORD || undefined,
  ssl: false
});

async function fixTestPasswords() {
  try {
    console.log('Generating bcrypt hash for TestPass123!...');
    const hash = await bcrypt.hash('TestPass123!', 12);
    console.log('Hash generated:', hash);
    
    console.log('Updating all test users with correct password hash...');
    const result = await pool.query(
      `UPDATE users SET password_hash = $1 
       WHERE auth_provider IN ('local', 'email') 
       AND (email LIKE '%@test.com' OR email = 'admin@befreefitness.com')`,
      [hash]
    );
    
    console.log(`Updated ${result.rowCount} users with correct password hash`);
    
    // Verify by listing updated users
    const users = await pool.query(
      `SELECT id, email, first_name, last_name FROM users 
       WHERE auth_provider IN ('local', 'email') 
       AND (email LIKE '%@test.com' OR email = 'admin@befreefitness.com')
       ORDER BY id`
    );
    
    console.log('\nUpdated users:');
    users.rows.forEach(user => {
      console.log(`- ${user.email} (${user.first_name} ${user.last_name})`);
    });
    
    await pool.end();
    console.log('\nDone!');
  } catch (error) {
    console.error('Error:', error);
    await pool.end();
    process.exit(1);
  }
}

fixTestPasswords();
