/**
 * MongoDB Test Data Fixtures
 * Provides reusable test data for MongoDB integration tests
 */

export const mongoTestUsers = [
  {
    name: 'Alice Smith',
    email: 'alice.test@example.com',
    age: 28,
    city: 'New York',
    active: true,
    tags: ['developer', 'javascript', 'typescript'],
    balance: 1000,
    createdAt: new Date('2024-01-15'),
  },
  {
    name: 'Bob Johnson',
    email: 'bob.test@example.com',
    age: 35,
    city: 'Los Angeles',
    active: true,
    tags: ['designer', 'ui-ux'],
    balance: 500,
    createdAt: new Date('2024-02-10'),
  },
  {
    name: 'Charlie Brown',
    email: 'charlie.test@example.com',
    age: 42,
    city: 'Chicago',
    active: false,
    tags: ['manager', 'devops'],
    balance: 750,
    createdAt: new Date('2024-03-05'),
  },
  {
    name: 'Diana Prince',
    email: 'diana.test@example.com',
    age: 30,
    city: 'New York',
    active: true,
    tags: ['developer', 'python', 'data-science'],
    balance: 1200,
    createdAt: new Date('2024-03-20'),
  },
];

export const mongoTestProducts = [
  {
    name: 'Laptop Pro 15',
    description: 'High-performance laptop for professional developers',
    price: 1299.99,
    category: 'Electronics',
    stock: 50,
    tags: ['laptop', 'professional', 'developer'],
    rating: 4.5,
  },
  {
    name: 'Wireless Mouse',
    description: 'Ergonomic wireless mouse with RGB lighting',
    price: 29.99,
    category: 'Accessories',
    stock: 200,
    tags: ['mouse', 'wireless', 'gaming'],
    rating: 4.2,
  },
  {
    name: 'Mechanical Keyboard',
    description: 'Professional mechanical keyboard with blue switches',
    price: 89.99,
    category: 'Accessories',
    stock: 75,
    tags: ['keyboard', 'mechanical', 'professional'],
    rating: 4.7,
  },
  {
    name: '4K Monitor',
    description: 'Ultra HD 27-inch monitor for developers',
    price: 399.99,
    category: 'Electronics',
    stock: 30,
    tags: ['monitor', '4k', 'display'],
    rating: 4.6,
  },
];

export const mongoTestOrders = [
  {
    orderId: 'TEST-ORD-001',
    customer: 'Alice Smith',
    customerId: 'alice.test@example.com',
    items: [
      { product: 'Laptop Pro 15', quantity: 1, price: 1299.99 },
    ],
    total: 1299.99,
    status: 'completed',
    orderDate: new Date('2024-01-20'),
  },
  {
    orderId: 'TEST-ORD-002',
    customer: 'Bob Johnson',
    customerId: 'bob.test@example.com',
    items: [
      { product: 'Wireless Mouse', quantity: 2, price: 29.99 },
      { product: 'Mechanical Keyboard', quantity: 1, price: 89.99 },
    ],
    total: 149.97,
    status: 'completed',
    orderDate: new Date('2024-02-15'),
  },
  {
    orderId: 'TEST-ORD-003',
    customer: 'Charlie Brown',
    customerId: 'charlie.test@example.com',
    items: [
      { product: '4K Monitor', quantity: 1, price: 399.99 },
    ],
    total: 399.99,
    status: 'pending',
    orderDate: new Date('2024-03-10'),
  },
];

export const mongoTestLocations = [
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
];

/**
 * Generate time series sensor data
 */
export function generateSensorData(count: number = 100): any[] {
  const now = new Date();
  const sensorData = [];

  for (let i = 0; i < count; i++) {
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

  return sensorData;
}

/**
 * Sample validated user schema
 */
export const validatedUserSchema = {
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
};
