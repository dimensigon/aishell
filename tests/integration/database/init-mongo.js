/**
 * MongoDB Initialization Script
 * Creates test database, collections, and sample data for integration tests
 */

// Switch to test database
db = db.getSiblingDB('test_integration_db');

print('🚀 Initializing MongoDB test database...');

// Create collections with sample data
print('📦 Creating users collection...');
db.createCollection('users');
db.users.insertMany([
  {
    name: 'Alice Smith',
    email: 'alice@example.com',
    age: 28,
    city: 'New York',
    active: true,
    tags: ['developer', 'javascript'],
    createdAt: new Date('2024-01-15'),
  },
  {
    name: 'Bob Johnson',
    email: 'bob@example.com',
    age: 35,
    city: 'Los Angeles',
    active: true,
    tags: ['designer', 'ui-ux'],
    createdAt: new Date('2024-02-10'),
  },
  {
    name: 'Charlie Brown',
    email: 'charlie@example.com',
    age: 42,
    city: 'Chicago',
    active: false,
    tags: ['manager', 'devops'],
    createdAt: new Date('2024-03-05'),
  },
]);

print('📦 Creating products collection...');
db.createCollection('products');
db.products.insertMany([
  {
    name: 'Laptop Pro 15',
    description: 'High-performance laptop for professional developers',
    price: 1299.99,
    category: 'Electronics',
    stock: 50,
    tags: ['laptop', 'professional', 'developer'],
  },
  {
    name: 'Wireless Mouse',
    description: 'Ergonomic wireless mouse with RGB lighting',
    price: 29.99,
    category: 'Accessories',
    stock: 200,
    tags: ['mouse', 'wireless', 'gaming'],
  },
  {
    name: 'Mechanical Keyboard',
    description: 'Professional mechanical keyboard with blue switches',
    price: 89.99,
    category: 'Accessories',
    stock: 75,
    tags: ['keyboard', 'mechanical', 'professional'],
  },
  {
    name: '4K Monitor',
    description: 'Ultra HD 27-inch monitor for developers',
    price: 399.99,
    category: 'Electronics',
    stock: 30,
    tags: ['monitor', '4k', 'display'],
  },
]);

print('📦 Creating orders collection...');
db.createCollection('orders');
db.orders.insertMany([
  {
    orderId: 'ORD-001',
    customer: 'Alice Smith',
    customerId: 'alice@example.com',
    items: [
      { product: 'Laptop Pro 15', quantity: 1, price: 1299.99 },
    ],
    total: 1299.99,
    status: 'completed',
    orderDate: new Date('2024-01-20'),
  },
  {
    orderId: 'ORD-002',
    customer: 'Bob Johnson',
    customerId: 'bob@example.com',
    items: [
      { product: 'Wireless Mouse', quantity: 2, price: 29.99 },
      { product: 'Mechanical Keyboard', quantity: 1, price: 89.99 },
    ],
    total: 149.97,
    status: 'completed',
    orderDate: new Date('2024-02-15'),
  },
  {
    orderId: 'ORD-003',
    customer: 'Charlie Brown',
    customerId: 'charlie@example.com',
    items: [
      { product: '4K Monitor', quantity: 1, price: 399.99 },
    ],
    total: 399.99,
    status: 'pending',
    orderDate: new Date('2024-03-10'),
  },
]);

print('📦 Creating locations collection with geospatial data...');
db.createCollection('locations');
db.locations.insertMany([
  {
    name: 'Main Office',
    address: '123 Tech Street, San Francisco, CA',
    location: {
      type: 'Point',
      coordinates: [-122.4194, 37.7749], // [longitude, latitude]
    },
    type: 'office',
  },
  {
    name: 'Warehouse',
    address: '456 Storage Ave, Oakland, CA',
    location: {
      type: 'Point',
      coordinates: [-122.2711, 37.8044],
    },
    type: 'warehouse',
  },
  {
    name: 'Retail Store',
    address: '789 Market St, San Francisco, CA',
    location: {
      type: 'Point',
      coordinates: [-122.4058, 37.7875],
    },
    type: 'retail',
  },
]);

// Create geospatial index
db.locations.createIndex({ location: '2dsphere' });
print('✅ Created 2dsphere index on locations');

print('📦 Creating sensor_data time series collection...');
db.createCollection('sensor_data', {
  timeseries: {
    timeField: 'timestamp',
    metaField: 'sensorId',
    granularity: 'minutes',
  },
});

// Insert sample sensor data
const now = new Date();
const sensorData = [];
for (let i = 0; i < 100; i++) {
  const timestamp = new Date(now.getTime() - i * 60000); // Every minute
  sensorData.push({
    sensorId: 'temp_sensor_1',
    timestamp: timestamp,
    temperature: 20 + Math.random() * 10,
    humidity: 50 + Math.random() * 20,
    location: 'Building A',
  });
  sensorData.push({
    sensorId: 'temp_sensor_2',
    timestamp: timestamp,
    temperature: 18 + Math.random() * 12,
    humidity: 45 + Math.random() * 25,
    location: 'Building B',
  });
}
db.sensor_data.insertMany(sensorData);
print('✅ Inserted 200 sensor data points');

// Create indexes for better query performance
print('🔍 Creating indexes...');

// Users indexes
db.users.createIndex({ email: 1 }, { unique: true });
db.users.createIndex({ city: 1, age: -1 });
db.users.createIndex({ active: 1 });
db.users.createIndex({ createdAt: 1 });

// Products indexes
db.products.createIndex({ name: 'text', description: 'text' });
db.products.createIndex({ category: 1, price: -1 });
db.products.createIndex({ tags: 1 });

// Orders indexes
db.orders.createIndex({ customerId: 1, orderDate: -1 });
db.orders.createIndex({ status: 1 });
db.orders.createIndex({ orderDate: -1 });

print('✅ Indexes created successfully');

// Create validated collection
print('📦 Creating validated collection with schema...');
db.createCollection('validated_users', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['name', 'email', 'age'],
      properties: {
        name: {
          bsonType: 'string',
          minLength: 1,
          maxLength: 100,
          description: 'must be a string and is required',
        },
        email: {
          bsonType: 'string',
          pattern: '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$',
          description: 'must be a valid email address',
        },
        age: {
          bsonType: 'int',
          minimum: 0,
          maximum: 150,
          description: 'must be an integer between 0 and 150',
        },
        status: {
          enum: ['active', 'inactive', 'pending'],
          description: 'can only be one of the enum values',
        },
      },
    },
  },
  validationLevel: 'strict',
  validationAction: 'error',
});
print('✅ Validated collection created');

// Create capped collection for logs
print('📦 Creating capped collection for logs...');
db.createCollection('logs', {
  capped: true,
  size: 5242880, // 5MB
  max: 5000, // Maximum 5000 documents
});
print('✅ Capped collection created');

// Display statistics
print('\n📊 Database Statistics:');
print('Users:', db.users.countDocuments());
print('Products:', db.products.countDocuments());
print('Orders:', db.orders.countDocuments());
print('Locations:', db.locations.countDocuments());
print('Sensor Data:', db.sensor_data.countDocuments());

print('\n✅ MongoDB initialization complete!');
print('🎯 Ready for integration tests\n');

// Show all collections
print('📋 Available collections:');
db.getCollectionNames().forEach(function (collection) {
  print('  - ' + collection);
});
