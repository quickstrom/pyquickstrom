// @ts-ignore
const [timeoutMs, done] = args;

function delay(ms: number): Promise<null> {
  return new Promise((resolve) => {
    setTimeout(resolve, ms);
  });
}

(function () {
  Promise.race([
    (window as any).quickstromChangeObserver,
    delay(timeoutMs),
  ]).then(done);
})();
