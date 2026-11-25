/**
 * Snapshot interpolation for state the server sends many times a second.
 *
 * Updates arrive with network jitter, and drawing each one as it arrives
 * looks jerky: frames between two updates show nothing new, and updates
 * that arrive in bursts make objects jump. Instead, every update is kept,
 * and each frame draws the state as it was `delay` ms ago, blended between
 * the two snapshots around that moment.
 *
 * Snapshots are placed on the sender's clock when updates carry the time
 * they were sent (push(values, arrivedAt, sentAt)): arrival times include
 * the jitter, sending times do not. The two clocks are tied by the smallest
 * (arrival - sent) seen recently, i.e. the fastest delivery. Without a
 * sending time, the arrival time is used.
 *
 * - A value that moves more than `snapDistance` between two snapshots
 *   jumps there instead of gliding (the ball going back to the center).
 * - When updates stop, motion continues from the last two snapshots for at
 *   most `maxExtrapolation` ms, then holds.
 *
 * Values are flat objects of numbers ({ballX, ballZ, ...}).
 */
export const createInterpolator = ({
  delay = 50,
  maxExtrapolation = 100,
  snapDistance = 1,
  keep = 1000,
  offsetWindow = 120,
  now = () => performance.now(),
} = {}) => {
  const snapshots = []; // {time: on the sender's clock, values}
  const offsets = []; // arrival - sent, most recent last

  const mix = (from, to, alpha) => {
    const out = {};
    for (const key of Object.keys(to)) {
      const a = from[key];
      const b = to[key];
      out[key] = a === undefined || Math.abs(b - a) > snapDistance ? b : a + (b - a) * alpha;
    }
    return out;
  };

  const offset = () => (offsets.length ? Math.min(...offsets) : 0);

  return {
    /**
     * Add the state that arrived at `arrivedAt` (ms, the clock of sample()),
     * sent at `sentAt` (ms on the sender's clock) when known.
     */
    push(values, arrivedAt = now(), sentAt = arrivedAt) {
      offsets.push(arrivedAt - sentAt);
      if (offsets.length > offsetWindow) offsets.shift();
      const last = snapshots[snapshots.length - 1];
      if (last && sentAt <= last.time) return; // out of order or repeated
      snapshots.push({ time: sentAt, values: { ...values } });
      // Drop what no render time can reach any more; keep at least two.
      while (snapshots.length > 2 && snapshots[1].time < sentAt - keep) snapshots.shift();
    },

    /** The state to draw at `time`, or null before the first update. */
    sample(time = now()) {
      if (snapshots.length === 0) return null;
      const target = time - offset() - delay;
      let i = snapshots.length - 1;
      while (i >= 0 && snapshots[i].time > target) i -= 1;
      if (i < 0) return { ...snapshots[0].values }; // not enough history yet

      const older = snapshots[i];
      const newer = snapshots[i + 1];
      if (newer) {
        const span = newer.time - older.time;
        return mix(older.values, newer.values, span > 0 ? (target - older.time) / span : 1);
      }
      // Past the newest update: continue the last motion for a short while.
      const previous = snapshots[i - 1];
      if (!previous) return { ...older.values };
      const span = older.time - previous.time;
      if (span <= 0) return { ...older.values };
      const ahead = Math.min(target - older.time, maxExtrapolation);
      return mix(previous.values, older.values, 1 + ahead / span);
    },

    /** Forget every snapshot. */
    clear() {
      snapshots.length = 0;
      offsets.length = 0;
    },

    get size() {
      return snapshots.length;
    },
  };
};
