// AI-Shell MongoDB Initialization Script
// Creates test database, collections, and sample data

// Switch to testdb
db = db.getSiblingDB('testdb');

// Create users collection with sample data
db.users.insertMany([
    {
        username: 'john_doe',
        email: 'john@example.com',
        fullName: 'John Doe',
        createdAt: new Date(),
        updatedAt: new Date(),
        isActive: true,
        profile: {
            age: 30,
            city: 'New York',
            country: 'USA'
        }
    },
    {
        username: 'jane_smith',
        email: 'jane@example.com',
        fullName: 'Jane Smith',
        createdAt: new Date(),
        updatedAt: new Date(),
        isActive: true,
        profile: {
            age: 28,
            city: 'San Francisco',
            country: 'USA'
        }
    },
    {
        username: 'bob_wilson',
        email: 'bob@example.com',
        fullName: 'Bob Wilson',
        createdAt: new Date(),
        updatedAt: new Date(),
        isActive: true,
        profile: {
            age: 35,
            city: 'London',
            country: 'UK'
        }
    },
    {
        username: 'alice_jones',
        email: 'alice@example.com',
        fullName: 'Alice Jones',
        createdAt: new Date(),
        updatedAt: new Date(),
        isActive: true,
        profile: {
            age: 27,
            city: 'Toronto',
            country: 'Canada'
        }
    },
    {
        username: 'charlie_brown',
        email: 'charlie@example.com',
        fullName: 'Charlie Brown',
        createdAt: new Date(),
        updatedAt: new Date(),
        isActive: false,
        profile: {
            age: 32,
            city: 'Sydney',
            country: 'Australia'
        }
    }
]);

// Create unique indexes on users collection
db.users.createIndex({ username: 1 }, { unique: true });
db.users.createIndex({ email: 1 }, { unique: true });
db.users.createIndex({ 'profile.city': 1 });

// Create products collection with sample data
db.products.insertMany([
    {
        name: 'Laptop',
        description: 'High-performance laptop',
        price: 999.99,
        stockQuantity: 50,
        category: 'Electronics',
        tags: ['computer', 'laptop', 'electronics'],
        specifications: {
            cpu: 'Intel i7',
            ram: '16GB',
            storage: '512GB SSD'
        },
        createdAt: new Date()
    },
    {
        name: 'Mouse',
        description: 'Wireless mouse',
        price: 29.99,
        stockQuantity: 200,
        category: 'Electronics',
        tags: ['mouse', 'wireless', 'accessory'],
        specifications: {
            type: 'Wireless',
            dpi: '1600'
        },
        createdAt: new Date()
    },
    {
        name: 'Keyboard',
        description: 'Mechanical keyboard',
        price: 79.99,
        stockQuantity: 150,
        category: 'Electronics',
        tags: ['keyboard', 'mechanical', 'accessory'],
        specifications: {
            type: 'Mechanical',
            switches: 'Cherry MX Blue'
        },
        createdAt: new Date()
    },
    {
        name: 'Monitor',
        description: '27-inch 4K monitor',
        price: 399.99,
        stockQuantity: 75,
        category: 'Electronics',
        tags: ['monitor', 'display', '4k'],
        specifications: {
            size: '27 inch',
            resolution: '3840x2160',
            refreshRate: '60Hz'
        },
        createdAt: new Date()
    },
    {
        name: 'Headphones',
        description: 'Noise-cancelling headphones',
        price: 199.99,
        stockQuantity: 100,
        category: 'Electronics',
        tags: ['headphones', 'audio', 'noise-cancelling'],
        specifications: {
            type: 'Over-ear',
            wireless: true,
            noiseCancelling: true
        },
        createdAt: new Date()
    },
    {
        name: 'Desk Chair',
        description: 'Ergonomic office chair',
        price: 299.99,
        stockQuantity: 30,
        category: 'Furniture',
        tags: ['chair', 'furniture', 'office'],
        specifications: {
            material: 'Mesh',
            adjustable: true,
            lumbarSupport: true
        },
        createdAt: new Date()
    },
    {
        name: 'Desk',
        description: 'Standing desk',
        price: 499.99,
        stockQuantity: 20,
        category: 'Furniture',
        tags: ['desk', 'furniture', 'standing'],
        specifications: {
            type: 'Standing',
            adjustable: true,
            maxHeight: '48 inches'
        },
        createdAt: new Date()
    },
    {
        name: 'Notebook',
        description: 'Spiral notebook pack',
        price: 9.99,
        stockQuantity: 500,
        category: 'Office Supplies',
        tags: ['notebook', 'stationery', 'paper'],
        specifications: {
            pages: 200,
            size: 'A4'
        },
        createdAt: new Date()
    },
    {
        name: 'Pen Set',
        description: 'Professional pen set',
        price: 19.99,
        stockQuantity: 300,
        category: 'Office Supplies',
        tags: ['pen', 'stationery', 'writing'],
        specifications: {
            quantity: 10,
            inkColor: 'Black'
        },
        createdAt: new Date()
    },
    {
        name: 'USB Cable',
        description: 'USB-C cable',
        price: 14.99,
        stockQuantity: 400,
        category: 'Electronics',
        tags: ['cable', 'usb', 'accessory'],
        specifications: {
            type: 'USB-C',
            length: '6 feet'
        },
        createdAt: new Date()
    }
]);

// Create indexes on products collection
db.products.createIndex({ name: 1 });
db.products.createIndex({ category: 1 });
db.products.createIndex({ tags: 1 });
db.products.createIndex({ price: 1 });

// Create orders collection with sample data
db.orders.insertMany([
    {
        userId: 'john_doe',
        items: [
            { productName: 'Laptop', quantity: 1, price: 999.99 },
            { productName: 'Mouse', quantity: 1, price: 29.99 }
        ],
        totalAmount: 1029.98,
        status: 'completed',
        orderDate: new Date(),
        shippingAddress: {
            street: '123 Main St',
            city: 'New York',
            state: 'NY',
            zipCode: '10001',
            country: 'USA'
        }
    },
    {
        userId: 'jane_smith',
        items: [
            { productName: 'Monitor', quantity: 1, price: 399.99 },
            { productName: 'Keyboard', quantity: 1, price: 79.99 }
        ],
        totalAmount: 479.98,
        status: 'pending',
        orderDate: new Date(),
        shippingAddress: {
            street: '456 Oak Ave',
            city: 'San Francisco',
            state: 'CA',
            zipCode: '94102',
            country: 'USA'
        }
    },
    {
        userId: 'john_doe',
        items: [
            { productName: 'Headphones', quantity: 1, price: 199.99 }
        ],
        totalAmount: 199.99,
        status: 'completed',
        orderDate: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000), // 7 days ago
        shippingAddress: {
            street: '123 Main St',
            city: 'New York',
            state: 'NY',
            zipCode: '10001',
            country: 'USA'
        }
    },
    {
        userId: 'bob_wilson',
        items: [
            { productName: 'Desk Chair', quantity: 2, price: 299.99 }
        ],
        totalAmount: 599.98,
        status: 'shipped',
        orderDate: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000), // 3 days ago
        shippingAddress: {
            street: '789 High St',
            city: 'London',
            zipCode: 'SW1A 1AA',
            country: 'UK'
        }
    }
]);

// Create indexes on orders collection
db.orders.createIndex({ userId: 1 });
db.orders.createIndex({ status: 1 });
db.orders.createIndex({ orderDate: -1 });

// Create reviews collection with sample data
db.reviews.insertMany([
    {
        productName: 'Laptop',
        userId: 'john_doe',
        rating: 5,
        title: 'Excellent laptop!',
        comment: 'Very fast and reliable. Great for development work.',
        helpful: 15,
        createdAt: new Date()
    },
    {
        productName: 'Mouse',
        userId: 'jane_smith',
        rating: 4,
        title: 'Good mouse',
        comment: 'Works well, but battery life could be better.',
        helpful: 8,
        createdAt: new Date()
    },
    {
        productName: 'Headphones',
        userId: 'bob_wilson',
        rating: 5,
        title: 'Amazing sound quality',
        comment: 'Best headphones I\'ve ever owned. Noise cancelling is superb.',
        helpful: 23,
        createdAt: new Date()
    },
    {
        productName: 'Monitor',
        userId: 'alice_jones',
        rating: 5,
        title: 'Crystal clear display',
        comment: 'Perfect for photo editing. Colors are accurate.',
        helpful: 12,
        createdAt: new Date()
    }
]);

// Create indexes on reviews collection
db.reviews.createIndex({ productName: 1 });
db.reviews.createIndex({ userId: 1 });
db.reviews.createIndex({ rating: -1 });

// Create a text index for full-text search
db.products.createIndex({ name: 'text', description: 'text' });

// Log initialization
print('AI-Shell MongoDB test database initialized successfully');
print('Database: testdb');
print('Collections: users, products, orders, reviews');
print('Sample data loaded');
print('Indexes created');
