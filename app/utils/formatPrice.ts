export function formatPrice(price: number): string {
  if (price < 0.0001) {
    return price.toExponential(2);
  } else if (price < 0.01) {
    return price.toFixed(4);
  } else {
    return price.toFixed(2);
  }
}