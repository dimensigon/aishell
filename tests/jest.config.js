module.exports = {
  testEnvironment: 'node',
  testMatch: ['**/?(*.)+(spec|test).[jt]s?(x)'],
  collectCoverage: true,
  coverageDirectory: './coverage-reports',
  coverageThreshold: {
    global: { branches: 75, functions: 80, lines: 80, statements: 80 }
  },
};
