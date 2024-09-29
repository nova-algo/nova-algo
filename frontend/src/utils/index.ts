export function shortenAddress(
  address: string,
  startLength = 5,
  endLength = 5
) {
  if (!address) return "";

  // Ensure the address is long enough to be shortened
  if (address.length <= startLength + endLength) {
    return address;
  }

  const start = address.slice(0, startLength);
  const end = address.slice(-endLength);

  return `${start}...${end}`;
}
