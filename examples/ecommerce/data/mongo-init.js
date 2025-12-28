// MongoDB initialization script for E-Commerce reviews and analytics

db = db.getSiblingDB('ecommerce');

// Create collections
db.createCollection('reviews');
db.createCollection('product_views');
db.createCollection('search_logs');
db.createCollection('error_logs');

// Reviews collection indexes
db.reviews.createIndex({ product_id: 1, created_at: -1 });
db.reviews.createIndex({ customer_id: 1 });
db.reviews.createIndex({ rating: 1 });
db.reviews.createIndex({ is_verified: 1 });
db.reviews.createIndex({ "sentiment.score": 1 });
db.reviews.createIndex({ created_at: -1 });

// Product views collection indexes (for analytics)
db.product_views.createIndex({ product_id: 1, timestamp: -1 });
db.product_views.createIndex({ customer_id: 1, timestamp: -1 });
db.product_views.createIndex({ timestamp: -1 });
db.product_views.createIndex({ session_id: 1 });

// Search logs collection indexes
db.search_logs.createIndex({ query: 1, timestamp: -1 });
db.search_logs.createIndex({ customer_id: 1, timestamp: -1 });
db.search_logs.createIndex({ timestamp: -1 });
db.search_logs.createIndex({ results_count: 1 });

// Error logs collection indexes
db.error_logs.createIndex({ timestamp: -1 });
db.error_logs.createIndex({ error_type: 1, timestamp: -1 });
db.error_logs.createIndex({ severity: 1, timestamp: -1 });

// Validation schemas
db.runCommand({
  collMod: 'reviews',
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['product_id', 'customer_id', 'rating', 'title', 'created_at'],
      properties: {
        product_id: {
          bsonType: 'int',
          description: 'must be an integer and is required'
        },
        customer_id: {
          bsonType: 'int',
          description: 'must be an integer and is required'
        },
        rating: {
          bsonType: 'int',
          minimum: 1,
          maximum: 5,
          description: 'must be an integer between 1 and 5 and is required'
        },
        title: {
          bsonType: 'string',
          maxLength: 200,
          description: 'must be a string and is required'
        },
        review_text: {
          bsonType: 'string',
          description: 'must be a string if the field exists'
        },
        is_verified: {
          bsonType: 'bool',
          description: 'indicates if this is a verified purchase'
        },
        helpful_count: {
          bsonType: 'int',
          minimum: 0,
          description: 'must be a non-negative integer'
        },
        sentiment: {
          bsonType: 'object',
          properties: {
            score: {
              bsonType: 'double',
              minimum: -1,
              maximum: 1
            },
            label: {
              enum: ['positive', 'neutral', 'negative']
            }
          }
        },
        created_at: {
          bsonType: 'date',
          description: 'must be a date and is required'
        }
      }
    }
  }
});

// Sample review data
const sampleReviews = [
  {
    product_id: 1,
    customer_id: 1,
    rating: 5,
    title: "Excellent product!",
    review_text: "This product exceeded my expectations. High quality and fast shipping.",
    is_verified: true,
    helpful_count: 12,
    sentiment: {
      score: 0.9,
      label: "positive"
    },
    images: ["https://example.com/review1_img1.jpg"],
    created_at: new Date("2024-10-15T10:30:00Z"),
    updated_at: new Date("2024-10-15T10:30:00Z")
  },
  {
    product_id: 1,
    customer_id: 2,
    rating: 4,
    title: "Good value for money",
    review_text: "Works as described. Minor issues with packaging but the product itself is great.",
    is_verified: true,
    helpful_count: 8,
    sentiment: {
      score: 0.6,
      label: "positive"
    },
    created_at: new Date("2024-10-20T14:20:00Z"),
    updated_at: new Date("2024-10-20T14:20:00Z")
  },
  {
    product_id: 2,
    customer_id: 3,
    rating: 2,
    title: "Disappointed",
    review_text: "Product quality is not as advertised. Would not recommend.",
    is_verified: true,
    helpful_count: 5,
    sentiment: {
      score: -0.7,
      label: "negative"
    },
    created_at: new Date("2024-10-25T09:15:00Z"),
    updated_at: new Date("2024-10-25T09:15:00Z")
  }
];

db.reviews.insertMany(sampleReviews);

// Sample product views data
const sampleViews = [
  {
    product_id: 1,
    customer_id: 1,
    session_id: "sess_abc123",
    page_type: "detail",
    referrer: "search",
    device: "desktop",
    timestamp: new Date("2024-10-27T10:00:00Z")
  },
  {
    product_id: 1,
    session_id: "sess_xyz789",
    page_type: "listing",
    referrer: "category",
    device: "mobile",
    timestamp: new Date("2024-10-27T10:05:00Z")
  }
];

db.product_views.insertMany(sampleViews);

// Sample search logs
const sampleSearches = [
  {
    query: "wireless headphones",
    customer_id: 1,
    session_id: "sess_abc123",
    results_count: 45,
    clicked_product_id: 15,
    timestamp: new Date("2024-10-27T09:30:00Z")
  },
  {
    query: "laptop stand",
    session_id: "sess_def456",
    results_count: 23,
    clicked_product_id: null,
    timestamp: new Date("2024-10-27T09:45:00Z")
  }
];

db.search_logs.insertMany(sampleSearches);

// Sample error logs
const sampleErrors = [
  {
    error_type: "payment_failed",
    severity: "error",
    message: "Payment gateway timeout",
    stack_trace: "Error at paymentService.process...",
    customer_id: 5,
    order_id: 1234,
    metadata: {
      payment_method: "credit_card",
      amount: 299.99
    },
    timestamp: new Date("2024-10-27T08:15:00Z")
  }
];

db.error_logs.insertMany(sampleErrors);

print("MongoDB initialization complete!");
print("Collections created: reviews, product_views, search_logs, error_logs");
print("Sample data inserted successfully");
