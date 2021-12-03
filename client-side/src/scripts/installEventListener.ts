import { awaitChanged, awaitLoaded, awaitStyleChanged } from "../events";

// @ts-ignore
const [queries, done] = args;

(function() {
    const selectors = Object.keys(queries);
    (window as any).quickstromEventsObserver = Promise.race([
        awaitLoaded(),
        awaitChanged(selectors),
        awaitStyleChanged(queries),
    ]);
    done();
})();
