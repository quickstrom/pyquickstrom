import { toDetached } from "../events";
import { queryState } from "../queries";

// @ts-ignore
const [queries, timeoutMs, done] = args;

function delay(ms: number): Promise<null> {
  return new Promise((resolve) => {
    setTimeout(resolve, ms);
  });
}

(function () {
  Promise.race([
    (window as any).quickstromEventsObserver,
    delay(timeoutMs),
  ]).then((events) => {
    if (events) {
      done({ events: events.map(toDetached), state: queryState(queries) });
    } else {
      done(null);
    }
  });
})();
