import { toArray } from "../arrays";
import { queryState } from "../queries";

function matchesSelector(node: Node, selector: string): boolean {
  return node instanceof Element && node.matches(selector);
}

function matchesAnySelector(node: Node, selectors: string[]): boolean {
    return selectors.find(selector => matchesSelector(node, selector)) !== undefined;
}

async function observeChange(selectors: string[]): Promise<void> {
  return new Promise((resolve) => {
    new MutationObserver((mutations, observer) => {
      const anyMatching = mutations
        .flatMap((mutation) => {
          return [
            [mutation.target],
            toArray(mutation.addedNodes) as Node[],
            toArray(mutation.removedNodes) as Node[],
          ].flat();
        })
        .some((node) => matchesAnySelector(node, selectors));

      if (anyMatching) {
        observer.disconnect();
        resolve();
      }
    }).observe(document, {
      childList: true,
      subtree: true,
      attributes: true,
    });
  });
}

// @ts-ignore
const [queries, done] = args;

(function () {
  (window as any).registeredObserver = observeChange(queries).then((_) =>
    queryState(queries)
  );
  done({ Right: [] });
})();
