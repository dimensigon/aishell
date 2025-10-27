// MongoDB Initialization Script
// This script sets up test databases, collections, indexes, and sample data

// Switch to test database
db = db.getSiblingDB('testdb');

// Drop existing collections if they exist
db.users.drop();
db.products.drop();
db.orders.drop();
db.reviews.drop();

print('Creating collections and inserting test data...');

// ====================================
// USERS Collection
// ====================================
db.users.insertMany([
  {
    _id: ObjectId(),
    username: 'john.doe',
    email: 'john.doe@example.com',
    firstName: 'John',
    lastName: 'Doe',
    age: 28,
    role: 'admin',
    active: true,
    createdAt: new Date('2024-01-15'),
    lastLogin: new Date('2025-10-26'),
    preferences: {
      theme: 'dark',
      notifications: true,
      language: 'en'
    },
    tags: ['developer', 'admin', 'premium']
  },
  {
    _id: ObjectId(),
    username: 'jane.smith',
    email: 'jane.smith@example.com',
    firstName: 'Jane',
    lastName: 'Smith',
    age: 32,
    role: 'user',
    active: true,
    createdAt: new Date('2024-03-20'),
    lastLogin: new Date('2025-10-25'),
    preferences: {
      theme: 'light',
      notifications: false,
      language: 'en'
    },
    tags: ['designer', 'premium']
  },
  {
    _id: ObjectId(),
    username: 'bob.wilson',
    email: 'bob.wilson@example.com',
    firstName: 'Bob',
    lastName: 'Wilson',
    age: 45,
    role: 'moderator',
    active: true,
    createdAt: new Date('2023-11-10'),
    lastLogin: new Date('2025-10-24'),
    preferences: {
      theme: 'dark',
      notifications: true,
      language: 'es'
    },
    tags: ['moderator', 'trusted']
  },
  {
    _id: ObjectId(),
    username: 'alice.johnson',
    email: 'alice.johnson@example.com',
    firstName: 'Alice',
    lastName: 'Johnson',
    age: 26,
    role: 'user',
    active: false,
    createdAt: new Date('2024-05-12'),
    lastLogin: new Date('2025-08-15'),
    preferences: {
      theme: 'light',
      notifications: true,
      language: 'fr'
    },
    tags: ['basic']
  },
  {
    _id: ObjectId(),
    username: 'charlie.brown',
    email: 'charlie.brown@example.com',
    firstName: 'Charlie',
    lastName: 'Brown',
    age: 35,
    role: 'user',
    active: true,
    createdAt: new Date('2024-02-28'),
    lastLogin: new Date('2025-10-27'),
    preferences: {
      theme: 'dark',
      notifications: false,
      language: 'de'
    },
    tags: ['premium', 'developer']
  }
]);

print('Inserted ' + db.users.countDocuments() + ' users');

// ====================================
// PRODUCTS Collection
// ====================================
db.products.insertMany([
  {
    _id: ObjectId(),
    sku: 'LAPTOP-001',
    name: 'MacBook Pro 16"',
    description: 'High-performance laptop for professionals',
    category: 'Electronics',
    subcategory: 'Laptops',
    price: 2499.99,
    cost: 1800.00,
    stock: 45,
    manufacturer: 'Apple',
    tags: ['premium', 'laptop', 'apple', 'pro'],
    specifications: {
      processor: 'M3 Pro',
      ram: '32GB',
      storage: '1TB SSD',
      display: '16.2 inch Retina'
    },
    ratings: {
      average: 4.8,
      count: 156
    },
    inStock: true,
    createdAt: new Date('2024-01-10'),
    updatedAt: new Date('2025-10-15')
  },
  {
    _id: ObjectId(),
    sku: 'PHONE-002',
    name: 'iPhone 15 Pro',
    description: 'Latest flagship smartphone',
    category: 'Electronics',
    subcategory: 'Smartphones',
    price: 999.99,
    cost: 650.00,
    stock: 120,
    manufacturer: 'Apple',
    tags: ['smartphone', 'apple', 'premium', '5g'],
    specifications: {
      processor: 'A17 Pro',
      ram: '8GB',
      storage: '256GB',
      display: '6.1 inch OLED'
    },
    ratings: {
      average: 4.7,
      count: 342
    },
    inStock: true,
    createdAt: new Date('2024-02-15'),
    updatedAt: new Date('2025-10-20')
  },
  {
    _id: ObjectId(),
    sku: 'DESK-003',
    name: 'Standing Desk Pro',
    description: 'Electric height-adjustable standing desk',
    category: 'Furniture',
    subcategory: 'Desks',
    price: 599.99,
    cost: 350.00,
    stock: 28,
    manufacturer: 'ErgoDesk',
    tags: ['furniture', 'desk', 'ergonomic', 'electric'],
    specifications: {
      material: 'Bamboo',
      dimensions: '60x30 inches',
      heightRange: '24-50 inches',
      weightCapacity: '300 lbs'
    },
    ratings: {
      average: 4.6,
      count: 89
    },
    inStock: true,
    createdAt: new Date('2024-03-01'),
    updatedAt: new Date('2025-10-10')
  },
  {
    _id: ObjectId(),
    sku: 'CHAIR-004',
    name: 'Ergonomic Office Chair',
    description: 'Premium ergonomic chair with lumbar support',
    category: 'Furniture',
    subcategory: 'Chairs',
    price: 449.99,
    cost: 280.00,
    stock: 0,
    manufacturer: 'ComfortSeating',
    tags: ['furniture', 'chair', 'ergonomic', 'office'],
    specifications: {
      material: 'Mesh and Foam',
      adjustments: 'Height, Arms, Lumbar, Tilt',
      weightCapacity: '350 lbs',
      warranty: '10 years'
    },
    ratings: {
      average: 4.9,
      count: 234
    },
    inStock: false,
    createdAt: new Date('2023-12-20'),
    updatedAt: new Date('2025-10-22')
  },
  {
    _id: ObjectId(),
    sku: 'MONITOR-005',
    name: '4K UHD Monitor 27"',
    description: 'Professional-grade 4K display',
    category: 'Electronics',
    subcategory: 'Monitors',
    price: 699.99,
    cost: 450.00,
    stock: 67,
    manufacturer: 'Dell',
    tags: ['monitor', '4k', 'professional', 'display'],
    specifications: {
      resolution: '3840x2160',
      size: '27 inch',
      panelType: 'IPS',
      refreshRate: '60Hz',
      ports: ['HDMI', 'DisplayPort', 'USB-C']
    },
    ratings: {
      average: 4.5,
      count: 178
    },
    inStock: true,
    createdAt: new Date('2024-01-25'),
    updatedAt: new Date('2025-10-18')
  },
  {
    _id: ObjectId(),
    sku: 'KEYBOARD-006',
    name: 'Mechanical Keyboard RGB',
    description: 'Gaming mechanical keyboard with RGB lighting',
    category: 'Electronics',
    subcategory: 'Keyboards',
    price: 149.99,
    cost: 75.00,
    stock: 95,
    manufacturer: 'Corsair',
    tags: ['keyboard', 'mechanical', 'gaming', 'rgb'],
    specifications: {
      switchType: 'Cherry MX Red',
      layout: 'Full-size',
      connectivity: 'Wired USB-C',
      features: ['RGB', 'Macro Keys', 'Media Controls']
    },
    ratings: {
      average: 4.4,
      count: 267
    },
    inStock: true,
    createdAt: new Date('2024-04-10'),
    updatedAt: new Date('2025-10-12')
  }
]);

print('Inserted ' + db.products.countDocuments() + ' products');

// ====================================
// ORDERS Collection
// ====================================
db.orders.insertMany([
  {
    _id: ObjectId(),
    orderNumber: 'ORD-2025-0001',
    userId: db.users.findOne({username: 'john.doe'})._id,
    items: [
      {
        productId: db.products.findOne({sku: 'LAPTOP-001'})._id,
        sku: 'LAPTOP-001',
        name: 'MacBook Pro 16"',
        quantity: 1,
        price: 2499.99,
        total: 2499.99
      },
      {
        productId: db.products.findOne({sku: 'KEYBOARD-006'})._id,
        sku: 'KEYBOARD-006',
        name: 'Mechanical Keyboard RGB',
        quantity: 1,
        price: 149.99,
        total: 149.99
      }
    ],
    subtotal: 2649.98,
    tax: 212.00,
    shipping: 0.00,
    total: 2861.98,
    status: 'delivered',
    paymentMethod: 'credit_card',
    shippingAddress: {
      street: '123 Main St',
      city: 'San Francisco',
      state: 'CA',
      zip: '94102',
      country: 'USA'
    },
    createdAt: new Date('2025-10-01'),
    shippedAt: new Date('2025-10-02'),
    deliveredAt: new Date('2025-10-05')
  },
  {
    _id: ObjectId(),
    orderNumber: 'ORD-2025-0002',
    userId: db.users.findOne({username: 'jane.smith'})._id,
    items: [
      {
        productId: db.products.findOne({sku: 'DESK-003'})._id,
        sku: 'DESK-003',
        name: 'Standing Desk Pro',
        quantity: 1,
        price: 599.99,
        total: 599.99
      },
      {
        productId: db.products.findOne({sku: 'CHAIR-004'})._id,
        sku: 'CHAIR-004',
        name: 'Ergonomic Office Chair',
        quantity: 1,
        price: 449.99,
        total: 449.99
      }
    ],
    subtotal: 1049.98,
    tax: 84.00,
    shipping: 49.99,
    total: 1183.97,
    status: 'processing',
    paymentMethod: 'paypal',
    shippingAddress: {
      street: '456 Oak Ave',
      city: 'New York',
      state: 'NY',
      zip: '10001',
      country: 'USA'
    },
    createdAt: new Date('2025-10-25'),
    shippedAt: null,
    deliveredAt: null
  },
  {
    _id: ObjectId(),
    orderNumber: 'ORD-2025-0003',
    userId: db.users.findOne({username: 'charlie.brown'})._id,
    items: [
      {
        productId: db.products.findOne({sku: 'MONITOR-005'})._id,
        sku: 'MONITOR-005',
        name: '4K UHD Monitor 27"',
        quantity: 2,
        price: 699.99,
        total: 1399.98
      }
    ],
    subtotal: 1399.98,
    tax: 112.00,
    shipping: 0.00,
    total: 1511.98,
    status: 'shipped',
    paymentMethod: 'credit_card',
    shippingAddress: {
      street: '789 Tech Blvd',
      city: 'Austin',
      state: 'TX',
      zip: '73301',
      country: 'USA'
    },
    createdAt: new Date('2025-10-20'),
    shippedAt: new Date('2025-10-22'),
    deliveredAt: null
  }
]);

print('Inserted ' + db.orders.countDocuments() + ' orders');

// ====================================
// REVIEWS Collection
// ====================================
db.reviews.insertMany([
  {
    _id: ObjectId(),
    productId: db.products.findOne({sku: 'LAPTOP-001'})._id,
    userId: db.users.findOne({username: 'john.doe'})._id,
    rating: 5,
    title: 'Excellent Performance!',
    comment: 'This laptop is incredibly fast and the display is stunning. Worth every penny!',
    verified: true,
    helpful: 45,
    notHelpful: 2,
    createdAt: new Date('2025-10-10'),
    updatedAt: new Date('2025-10-10')
  },
  {
    _id: ObjectId(),
    productId: db.products.findOne({sku: 'PHONE-002'})._id,
    userId: db.users.findOne({username: 'jane.smith'})._id,
    rating: 4,
    title: 'Great phone, minor issues',
    comment: 'Love the camera quality and battery life. Sometimes gets warm during gaming.',
    verified: true,
    helpful: 23,
    notHelpful: 5,
    createdAt: new Date('2025-10-15'),
    updatedAt: new Date('2025-10-15')
  },
  {
    _id: ObjectId(),
    productId: db.products.findOne({sku: 'KEYBOARD-006'})._id,
    userId: db.users.findOne({username: 'charlie.brown'})._id,
    rating: 5,
    title: 'Best keyboard I\'ve owned',
    comment: 'The mechanical switches feel great and the RGB lighting is customizable. Highly recommend!',
    verified: true,
    helpful: 67,
    notHelpful: 1,
    createdAt: new Date('2025-10-08'),
    updatedAt: new Date('2025-10-08')
  }
]);

print('Inserted ' + db.reviews.countDocuments() + ' reviews');

// ====================================
// CREATE INDEXES
// ====================================
print('Creating indexes...');

// Users indexes
db.users.createIndex({ username: 1 }, { unique: true });
db.users.createIndex({ email: 1 }, { unique: true });
db.users.createIndex({ role: 1 });
db.users.createIndex({ active: 1 });
db.users.createIndex({ createdAt: -1 });

// Products indexes
db.products.createIndex({ sku: 1 }, { unique: true });
db.products.createIndex({ name: 'text', description: 'text' });
db.products.createIndex({ category: 1, subcategory: 1 });
db.products.createIndex({ price: 1 });
db.products.createIndex({ 'ratings.average': -1 });
db.products.createIndex({ tags: 1 });
db.products.createIndex({ inStock: 1 });

// Orders indexes
db.orders.createIndex({ orderNumber: 1 }, { unique: true });
db.orders.createIndex({ userId: 1 });
db.orders.createIndex({ status: 1 });
db.orders.createIndex({ createdAt: -1 });
db.orders.createIndex({ 'items.productId': 1 });

// Reviews indexes
db.reviews.createIndex({ productId: 1 });
db.reviews.createIndex({ userId: 1 });
db.reviews.createIndex({ rating: -1 });
db.reviews.createIndex({ createdAt: -1 });
db.reviews.createIndex({ verified: 1 });

print('✓ MongoDB initialization complete!');
print('Database: testdb');
print('Collections created: users, products, orders, reviews');
print('Indexes created for optimized queries');
