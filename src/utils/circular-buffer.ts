/**
 * Circular Buffer
 * Efficient bounded buffer with O(1) push operations and fixed memory footprint
 * Prevents unbounded array growth and memory leaks
 */

/**
 * CircularBuffer implementation with fixed capacity
 * @template T The type of elements stored in the buffer
 */
export class CircularBuffer<T> {
  private buffer: T[];
  private head: number = 0;
  private tail: number = 0;
  private size: number = 0;
  private readonly capacity: number;

  /**
   * Create a new circular buffer
   * @param capacity Maximum number of items to store
   * @throws {Error} If capacity is not a positive integer
   */
  constructor(capacity: number) {
    if (capacity <= 0 || !Number.isInteger(capacity)) {
      throw new Error('Capacity must be a positive integer');
    }

    this.capacity = capacity;
    this.buffer = new Array(capacity);
  }

  /**
   * Add an item to the buffer
   * If buffer is full, overwrites the oldest item
   * Time complexity: O(1)
   * @param item The item to add
   */
  push(item: T): void {
    this.buffer[this.tail] = item;
    this.tail = (this.tail + 1) % this.capacity;

    if (this.size < this.capacity) {
      this.size++;
    } else {
      // Buffer is full, move head forward
      this.head = (this.head + 1) % this.capacity;
    }
  }

  /**
   * Convert buffer to array in chronological order (oldest to newest)
   * Time complexity: O(n)
   * @returns Array containing all items in order
   */
  toArray(): T[] {
    if (this.size === 0) return [];

    const result: T[] = [];
    for (let i = 0; i < this.size; i++) {
      result.push(this.buffer[(this.head + i) % this.capacity]);
    }
    return result;
  }

  /**
   * Get a slice of the buffer
   * Time complexity: O(n)
   * @param start Start index (inclusive)
   * @param end End index (exclusive)
   * @returns Array containing the sliced items
   */
  slice(start: number, end?: number): T[] {
    return this.toArray().slice(start, end);
  }

  /**
   * Get the number of items currently in the buffer
   * Time complexity: O(1)
   */
  get length(): number {
    return this.size;
  }

  /**
   * Get the maximum capacity of the buffer
   * Time complexity: O(1)
   */
  get maxCapacity(): number {
    return this.capacity;
  }

  /**
   * Check if the buffer is empty
   * Time complexity: O(1)
   */
  isEmpty(): boolean {
    return this.size === 0;
  }

  /**
   * Check if the buffer is full
   * Time complexity: O(1)
   */
  isFull(): boolean {
    return this.size === this.capacity;
  }

  /**
   * Clear all items from the buffer
   * Time complexity: O(1)
   */
  clear(): void {
    this.head = 0;
    this.tail = 0;
    this.size = 0;
    // Don't need to clear buffer array - items will be overwritten
  }

  /**
   * Get the most recent item (without removing it)
   * Time complexity: O(1)
   * @returns The most recent item, or undefined if buffer is empty
   */
  peek(): T | undefined {
    if (this.size === 0) return undefined;
    const lastIndex = (this.tail - 1 + this.capacity) % this.capacity;
    return this.buffer[lastIndex];
  }

  /**
   * Get the oldest item (without removing it)
   * Time complexity: O(1)
   * @returns The oldest item, or undefined if buffer is empty
   */
  peekOldest(): T | undefined {
    if (this.size === 0) return undefined;
    return this.buffer[this.head];
  }

  /**
   * Get item at specific index (0 = oldest, length-1 = newest)
   * Time complexity: O(1)
   * @param index Index to access
   * @returns The item at the index, or undefined if out of bounds
   */
  at(index: number): T | undefined {
    if (index < 0 || index >= this.size) return undefined;
    return this.buffer[(this.head + index) % this.capacity];
  }

  /**
   * Iterate over all items in chronological order
   * @param callback Function to call for each item
   */
  forEach(callback: (item: T, index: number) => void): void {
    for (let i = 0; i < this.size; i++) {
      callback(this.buffer[(this.head + i) % this.capacity], i);
    }
  }

  /**
   * Map over all items and return new array
   * Time complexity: O(n)
   * @param callback Function to transform each item
   * @returns New array with transformed items
   */
  map<U>(callback: (item: T, index: number) => U): U[] {
    const result: U[] = [];
    for (let i = 0; i < this.size; i++) {
      result.push(callback(this.buffer[(this.head + i) % this.capacity], i));
    }
    return result;
  }

  /**
   * Filter items based on predicate
   * Time complexity: O(n)
   * @param predicate Function to test each item
   * @returns New array with items that pass the test
   */
  filter(predicate: (item: T, index: number) => boolean): T[] {
    const result: T[] = [];
    for (let i = 0; i < this.size; i++) {
      const item = this.buffer[(this.head + i) % this.capacity];
      if (predicate(item, i)) {
        result.push(item);
      }
    }
    return result;
  }

  /**
   * Get memory usage statistics
   * @returns Object with memory statistics
   */
  getMemoryStats(): {
    capacity: number;
    size: number;
    utilizationPercent: number;
    estimatedBytes: number;
  } {
    return {
      capacity: this.capacity,
      size: this.size,
      utilizationPercent: (this.size / this.capacity) * 100,
      estimatedBytes: this.capacity * 8 // Rough estimate: pointer size
    };
  }
}
