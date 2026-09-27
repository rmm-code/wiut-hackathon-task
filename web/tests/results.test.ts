import assert from 'node:assert/strict';
import { test } from 'node:test';
import { parseResults } from '../src/lib/results.ts';

const file = (events: unknown[], risk: unknown[] = []) => ({ videos: { 'clip.mp4': { events, risk } } });

test('imports official tuples without inventing confidence or lane data', () => {
  const result = parseResults(file([[1, 3, 'near_miss'], [2, 4, 'jaywalking']], [[0, 0.1], [1, 0.7]]), 'clip.mp4', 10);
  assert.equal(result.events.length, 2);
  assert.equal(result.events[0].confidence, undefined);
  assert.equal(result.events[0].lane, undefined);
});

test('accepts a valid empty result and events touching at their boundaries', () => {
  assert.deepEqual(parseResults(file([]), 'clip.mp4', 10).events, []);
  assert.equal(parseResults(file([[1, 3, 'near_miss'], [3, 5, 'near_miss']]), 'clip.mp4', 10).events.length, 2);
});

test('requires the exact video filename', () => {
  assert.throws(() => parseResults(file([]), 'other.mp4', 10), /filename must match/);
});

test('rejects reversed, nonfinite, and out-of-video event times', () => {
  for (const event of [[3, 1, 'accident'], [1, 12, 'accident'], [NaN, 2, 'accident'], [-1, 3, 'accident'], [1, Infinity, 'accident']]) {
    assert.throws(() => parseResults(file([event]), 'clip.mp4', 10), /invalid timestamps/);
  }
});

test('rejects unknown classes and same-class overlap even when unsorted', () => {
  assert.throws(() => parseResults(file([[1, 3, 'speeding']]), 'clip.mp4', 10), /unknown class/);
  assert.throws(() => parseResults(file([[4, 8, 'near_miss'], [1, 5, 'near_miss']]), 'clip.mp4', 10), /Overlapping/);
});

test('rejects malformed, unordered, out-of-range, and nonfinite risk data', () => {
  for (const risk of [[[0, 1.1]], [[2, 0.5], [1, 0.4]], [[12, 0.2]], [[0, NaN]], [['0', 0.2]], [[0]]]) {
    assert.throws(() => parseResults(file([], risk), 'clip.mp4', 10), /Risk timestamps/);
  }
  assert.throws(() => parseResults({ videos: { 'clip.mp4': { events: [], risk: {} } } }, 'clip.mp4', 10), /Risk must be/);
});
