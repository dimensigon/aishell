/**
 * Migration: Create {{table_name}} table
 * Created: {{timestamp}}
 */

/**
 * Run the migration
 * @param {DatabaseConnectionManager} dbManager
 */
export async function up(dbManager) {
  // Create table
  await dbManager.executeQuery(`
    CREATE TABLE {{table_name}} (
      id SERIAL PRIMARY KEY,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
  `);

  // Create indexes
  await dbManager.executeQuery(`
    CREATE INDEX idx_{{table_name}}_created_at ON {{table_name}}(created_at)
  `);

  console.log('Table {{table_name}} created successfully');
}

/**
 * Rollback the migration
 * @param {DatabaseConnectionManager} dbManager
 */
export async function down(dbManager) {
  await dbManager.executeQuery('DROP TABLE IF EXISTS {{table_name}} CASCADE');
  console.log('Table {{table_name}} dropped successfully');
}
