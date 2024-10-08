import { NextApiRequest, NextApiResponse } from "next/types";

export function formatNumber(value: number): string {
  if (value >= 1000000) {
    return (value / 1000000).toFixed(1) + "M";
  } else if (value >= 1000) {
    return (value / 1000).toFixed(1) + "K";
  } else {
    return value.toString();
  }
}
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
export type HTTP_METHOD = "GET" | "PUT" | "POST" | "DELETE";
export type HTTP_METHOD_CB = (
  req: NextApiRequest,
  res: NextApiResponse
) => Promise<void>;
export async function mainHandler(
  req: NextApiRequest,
  res: NextApiResponse,
  {
    GET,
    PUT,
    POST,
    DELETE,
  }: {
    GET?: HTTP_METHOD_CB;
    POST?: HTTP_METHOD_CB;
    PUT?: HTTP_METHOD_CB;
    DELETE?: HTTP_METHOD_CB;
  }
) {
  const method = req.method as HTTP_METHOD;
  switch (method) {
    case "GET":
      return await GET?.(req, res);
    case "POST":
      return await POST?.(req, res);
    case "PUT":
      return PUT?.(req, res);
    case "DELETE":
      return DELETE?.(req, res);

    default:
      return res.status(405).end();
  }
}
type QueryParams = Record<string, string | number | boolean | null | undefined>;

export function objectToQueryParams(obj: QueryParams): string {
  const params = new URLSearchParams();

  Object.entries(obj).forEach(([key, value]) => {
    if (value !== null && value !== undefined) {
      params.append(key, value.toString());
    }
  });

  return params.toString();
}
