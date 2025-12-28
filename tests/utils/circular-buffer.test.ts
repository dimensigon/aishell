/**
 * CircularBuffer Tests
 * Comprehensive test suite for circular buffer implementation
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { CircularBuffer } from '../../src/utils/circular-buffer';

describe('CircularBuffer', () => {
  describe('Constructor', () => {
    it('should create buffer with valid capacity', () => {
      const buffer = new CircularBuffer<number>(10);
      expect(buffer.length).toBe(0);
      expect(buffer.maxCapacity).toBe(10);
    });

    it('should throw error for non-positive capacity', () => {
      expect(() => new CircularBuffer<number>(0)).toThrow('Capacity must be a positive integer');
      expect(() => new CircularBuffer<number>(-5)).toThrow('Capacity must be a positive integer');
    });

    it('should throw error for non-integer capacity', () => {
      expect(() => new CircularBuffer<number>(10.5)).toThrow('Capacity must be a positive integer');
    });
  });

  describe('push()', () => {
    let buffer: CircularBuffer<number>;

    beforeEach(() => {
      buffer = new CircularBuffer<number>(5);
    });

    it('should add items to buffer', () => {
      buffer.push(1);
      buffer.push(2);
      buffer.push(3);

      expect(buffer.length).toBe(3);
      expect(buffer.toArray()).toEqual([1, 2, 3]);
    });

    it('should overwrite oldest item when full', () => {
      buffer.push(1);
      buffer.push(2);
      buffer.push(3);
      buffer.push(4);
      buffer.push(5);

      expect(buffer.length).toBe(5);
      expect(buffer.toArray()).toEqual([1, 2, 3, 4, 5]);

      // Add one more - should overwrite 1
      buffer.push(6);
      expect(buffer.length).toBe(5);
      expect(buffer.toArray()).toEqual([2, 3, 4, 5, 6]);
    });

    it('should handle continuous wrapping', () => {
      // Fill and wrap multiple times
      for (let i = 1; i <= 15; i++) {
        buffer.push(i);
      }

      expect(buffer.length).toBe(5);
      expect(buffer.toArray()).toEqual([11, 12, 13, 14, 15]);
    });

    it('should maintain O(1) performance', () => {
      const largeBuffer = new CircularBuffer<number>(10000);

      const start = Date.now();
      for (let i = 0; i < 100000; i++) {
        largeBuffer.push(i);
      }
      const elapsed = Date.now() - start;

      // Should complete very quickly (< 100ms for 100k operations)
      expect(elapsed).toBeLessThan(100);
      expect(largeBuffer.length).toBe(10000);
    });
  });

  describe('toArray()', () => {
    let buffer: CircularBuffer<number>;

    beforeEach(() => {
      buffer = new CircularBuffer<number>(5);
    });

    it('should return empty array for empty buffer', () => {
      expect(buffer.toArray()).toEqual([]);
    });

    it('should return items in chronological order', () => {
      buffer.push(1);
      buffer.push(2);
      buffer.push(3);

      expect(buffer.toArray()).toEqual([1, 2, 3]);
    });

    it('should return correct order after wrapping', () => {
      buffer.push(1);
      buffer.push(2);
      buffer.push(3);
      buffer.push(4);
      buffer.push(5);
      buffer.push(6); // Overwrites 1
      buffer.push(7); // Overwrites 2

      expect(buffer.toArray()).toEqual([3, 4, 5, 6, 7]);
    });
  });

  describe('slice()', () => {
    let buffer: CircularBuffer<number>;

    beforeEach(() => {
      buffer = new CircularBuffer<number>(10);
      for (let i = 1; i <= 8; i++) {
        buffer.push(i);
      }
    });

    it('should slice from start', () => {
      expect(buffer.slice(0, 3)).toEqual([1, 2, 3]);
    });

    it('should slice from middle', () => {
      expect(buffer.slice(3, 6)).toEqual([4, 5, 6]);
    });

    it('should slice to end with no end param', () => {
      expect(buffer.slice(5)).toEqual([6, 7, 8]);
    });

    it('should handle negative indices', () => {
      expect(buffer.slice(-3)).toEqual([6, 7, 8]);
    });

    it('should work after wrapping', () => {
      const wrappedBuffer = new CircularBuffer<number>(5);
      for (let i = 1; i <= 8; i++) {
        wrappedBuffer.push(i);
      }

      expect(wrappedBuffer.slice(0, 3)).toEqual([4, 5, 6]);
    });
  });

  describe('length property', () => {
    let buffer: CircularBuffer<number>;

    beforeEach(() => {
      buffer = new CircularBuffer<number>(5);
    });

    it('should start at 0', () => {
      expect(buffer.length).toBe(0);
    });

    it('should increase as items are added', () => {
      buffer.push(1);
      expect(buffer.length).toBe(1);

      buffer.push(2);
      expect(buffer.length).toBe(2);
    });

    it('should cap at capacity', () => {
      for (let i = 0; i < 10; i++) {
        buffer.push(i);
      }

      expect(buffer.length).toBe(5);
    });
  });

  describe('isEmpty()', () => {
    let buffer: CircularBuffer<number>;

    beforeEach(() => {
      buffer = new CircularBuffer<number>(5);
    });

    it('should return true for empty buffer', () => {
      expect(buffer.isEmpty()).toBe(true);
    });

    it('should return false after adding items', () => {
      buffer.push(1);
      expect(buffer.isEmpty()).toBe(false);
    });

    it('should return true after clearing', () => {
      buffer.push(1);
      buffer.clear();
      expect(buffer.isEmpty()).toBe(true);
    });
  });

  describe('isFull()', () => {
    let buffer: CircularBuffer<number>;

    beforeEach(() => {
      buffer = new CircularBuffer<number>(3);
    });

    it('should return false for empty buffer', () => {
      expect(buffer.isFull()).toBe(false);
    });

    it('should return false for partially filled buffer', () => {
      buffer.push(1);
      buffer.push(2);
      expect(buffer.isFull()).toBe(false);
    });

    it('should return true when full', () => {
      buffer.push(1);
      buffer.push(2);
      buffer.push(3);
      expect(buffer.isFull()).toBe(true);
    });

    it('should remain true after wrapping', () => {
      buffer.push(1);
      buffer.push(2);
      buffer.push(3);
      buffer.push(4);
      expect(buffer.isFull()).toBe(true);
    });
  });

  describe('clear()', () => {
    let buffer: CircularBuffer<number>;

    beforeEach(() => {
      buffer = new CircularBuffer<number>(5);
      buffer.push(1);
      buffer.push(2);
      buffer.push(3);
    });

    it('should reset buffer to empty state', () => {
      buffer.clear();

      expect(buffer.length).toBe(0);
      expect(buffer.isEmpty()).toBe(true);
      expect(buffer.toArray()).toEqual([]);
    });

    it('should allow adding after clear', () => {
      buffer.clear();
      buffer.push(10);

      expect(buffer.length).toBe(1);
      expect(buffer.toArray()).toEqual([10]);
    });
  });

  describe('peek()', () => {
    let buffer: CircularBuffer<number>;

    beforeEach(() => {
      buffer = new CircularBuffer<number>(5);
    });

    it('should return undefined for empty buffer', () => {
      expect(buffer.peek()).toBeUndefined();
    });

    it('should return most recent item', () => {
      buffer.push(1);
      buffer.push(2);
      buffer.push(3);

      expect(buffer.peek()).toBe(3);
    });

    it('should not remove item', () => {
      buffer.push(1);
      buffer.push(2);

      expect(buffer.peek()).toBe(2);
      expect(buffer.length).toBe(2);
      expect(buffer.peek()).toBe(2);
    });

    it('should work after wrapping', () => {
      for (let i = 1; i <= 8; i++) {
        buffer.push(i);
      }

      expect(buffer.peek()).toBe(8);
    });
  });

  describe('peekOldest()', () => {
    let buffer: CircularBuffer<number>;

    beforeEach(() => {
      buffer = new CircularBuffer<number>(5);
    });

    it('should return undefined for empty buffer', () => {
      expect(buffer.peekOldest()).toBeUndefined();
    });

    it('should return oldest item', () => {
      buffer.push(1);
      buffer.push(2);
      buffer.push(3);

      expect(buffer.peekOldest()).toBe(1);
    });

    it('should update after wrapping', () => {
      for (let i = 1; i <= 8; i++) {
        buffer.push(i);
      }

      expect(buffer.peekOldest()).toBe(4);
    });
  });

  describe('at()', () => {
    let buffer: CircularBuffer<number>;

    beforeEach(() => {
      buffer = new CircularBuffer<number>(10);
      for (let i = 1; i <= 5; i++) {
        buffer.push(i);
      }
    });

    it('should access items by index', () => {
      expect(buffer.at(0)).toBe(1);
      expect(buffer.at(2)).toBe(3);
      expect(buffer.at(4)).toBe(5);
    });

    it('should return undefined for out of bounds', () => {
      expect(buffer.at(-1)).toBeUndefined();
      expect(buffer.at(5)).toBeUndefined();
      expect(buffer.at(100)).toBeUndefined();
    });

    it('should work after wrapping', () => {
      const wrappedBuffer = new CircularBuffer<number>(3);
      for (let i = 1; i <= 5; i++) {
        wrappedBuffer.push(i);
      }

      expect(wrappedBuffer.at(0)).toBe(3);
      expect(wrappedBuffer.at(1)).toBe(4);
      expect(wrappedBuffer.at(2)).toBe(5);
    });
  });

  describe('forEach()', () => {
    let buffer: CircularBuffer<number>;

    beforeEach(() => {
      buffer = new CircularBuffer<number>(5);
      buffer.push(1);
      buffer.push(2);
      buffer.push(3);
    });

    it('should iterate over all items', () => {
      const items: number[] = [];
      buffer.forEach(item => items.push(item));

      expect(items).toEqual([1, 2, 3]);
    });

    it('should provide index', () => {
      const indices: number[] = [];
      buffer.forEach((_, index) => indices.push(index));

      expect(indices).toEqual([0, 1, 2]);
    });

    it('should handle wrapped buffer', () => {
      for (let i = 4; i <= 8; i++) {
        buffer.push(i);
      }

      const items: number[] = [];
      buffer.forEach(item => items.push(item));

      expect(items).toEqual([4, 5, 6, 7, 8]);
    });
  });

  describe('map()', () => {
    let buffer: CircularBuffer<number>;

    beforeEach(() => {
      buffer = new CircularBuffer<number>(5);
      buffer.push(1);
      buffer.push(2);
      buffer.push(3);
    });

    it('should transform items', () => {
      const doubled = buffer.map(x => x * 2);
      expect(doubled).toEqual([2, 4, 6]);
    });

    it('should work with different types', () => {
      const strings = buffer.map(x => `value: ${x}`);
      expect(strings).toEqual(['value: 1', 'value: 2', 'value: 3']);
    });

    it('should provide index', () => {
      const withIndex = buffer.map((x, i) => ({ value: x, index: i }));
      expect(withIndex).toEqual([
        { value: 1, index: 0 },
        { value: 2, index: 1 },
        { value: 3, index: 2 }
      ]);
    });
  });

  describe('filter()', () => {
    let buffer: CircularBuffer<number>;

    beforeEach(() => {
      buffer = new CircularBuffer<number>(10);
      for (let i = 1; i <= 8; i++) {
        buffer.push(i);
      }
    });

    it('should filter items by predicate', () => {
      const evens = buffer.filter(x => x % 2 === 0);
      expect(evens).toEqual([2, 4, 6, 8]);
    });

    it('should return empty array if none match', () => {
      const large = buffer.filter(x => x > 100);
      expect(large).toEqual([]);
    });

    it('should return all if all match', () => {
      const all = buffer.filter(x => x > 0);
      expect(all).toEqual([1, 2, 3, 4, 5, 6, 7, 8]);
    });
  });

  describe('getMemoryStats()', () => {
    it('should return accurate statistics', () => {
      const buffer = new CircularBuffer<number>(100);

      for (let i = 0; i < 50; i++) {
        buffer.push(i);
      }

      const stats = buffer.getMemoryStats();

      expect(stats.capacity).toBe(100);
      expect(stats.size).toBe(50);
      expect(stats.utilizationPercent).toBe(50);
      expect(stats.estimatedBytes).toBeGreaterThan(0);
    });

    it('should show 100% utilization when full', () => {
      const buffer = new CircularBuffer<number>(10);

      for (let i = 0; i < 15; i++) {
        buffer.push(i);
      }

      const stats = buffer.getMemoryStats();
      expect(stats.utilizationPercent).toBe(100);
    });
  });

  describe('Memory Bounds', () => {
    it('should maintain fixed memory footprint', () => {
      const buffer = new CircularBuffer<number>(1000);

      // Add way more items than capacity
      for (let i = 0; i < 100000; i++) {
        buffer.push(i);
      }

      // Should never exceed capacity
      expect(buffer.length).toBe(1000);

      // Should contain last 1000 items
      const array = buffer.toArray();
      expect(array[0]).toBe(99000);
      expect(array[999]).toBe(99999);
    });

    it('should prevent memory leaks with continuous usage', () => {
      const buffer = new CircularBuffer<{ data: number[] }>(100);

      // Simulate long-running process
      for (let i = 0; i < 10000; i++) {
        buffer.push({ data: new Array(100).fill(i) });
      }

      // Memory is bounded by capacity
      expect(buffer.length).toBe(100);

      // Can still access all items
      const stats = buffer.getMemoryStats();
      expect(stats.utilizationPercent).toBe(100);
    });
  });

  describe('Type Safety', () => {
    it('should work with complex objects', () => {
      interface Metric {
        timestamp: number;
        value: number;
        tags: string[];
      }

      const buffer = new CircularBuffer<Metric>(5);

      buffer.push({ timestamp: 1, value: 100, tags: ['cpu'] });
      buffer.push({ timestamp: 2, value: 200, tags: ['memory'] });

      const metrics = buffer.toArray();
      expect(metrics[0].tags).toEqual(['cpu']);
      expect(metrics[1].value).toBe(200);
    });

    it('should maintain type through transformations', () => {
      const buffer = new CircularBuffer<string>(5);
      buffer.push('a');
      buffer.push('b');
      buffer.push('c');

      const lengths: number[] = buffer.map(s => s.length);
      expect(lengths).toEqual([1, 1, 1]);

      const filtered: string[] = buffer.filter(s => s > 'a');
      expect(filtered).toEqual(['b', 'c']);
    });
  });
});
