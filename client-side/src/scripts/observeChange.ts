import { toArray } from "../arrays";
import { queryState } from "../queries";

function matchesSelector(node: Node, selector: string): boolean {
  return node instanceof Element && node.matches(selector);
}

function matchesAnySelector(node: Node, selectors: string[]): boolean {
    return selectors.find(selector => matchesSelector(node, selector)) !== undefined;
}

async function observeChange(selectors: string[]): Promise<Element[]> {
  return new Promise((resolve) => {
    new MutationObserver((mutations, observer) => {
      const matching = mutations
        .flatMap((mutation) => {
          return [
            [mutation.target],
            toArray(mutation.addedNodes) as Node[],
            toArray(mutation.removedNodes) as Node[],
          ].flat();
        })
        .filter((node) => matchesAnySelector(node, selectors));

      const unique = new Set()
      matching.forEach(n => unique.add(n))

      if (unique.size > 0) {
        observer.disconnect();
        resolve(Array.from(unique) as Element[]);
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
  observeChange(Object.keys(queries)).then((elements) => {
    done({ elements, state: queryState(queries) })
  });
})();
