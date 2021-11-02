export function isElementInteractable(element: Element) {
  function belongsToElement(subElement: Element | null) {
    return element == subElement || element.contains(subElement);
  }
  const rec = element.getBoundingClientRect();

  const topLeft = document.elementFromPoint(rec.left, rec.top);
  const center = document.elementFromPoint(
    rec.left + rec.width / 2,
    rec.top + rec.height / 2
  );
  const bottomRight = document.elementFromPoint(
    rec.left + rec.width + 1,
    rec.top + rec.height + 1
  );

  return (
    belongsToElement(topLeft) ||
    belongsToElement(center) ||
    belongsToElement(bottomRight)
  );
}
