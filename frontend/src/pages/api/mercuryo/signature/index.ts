import { createHash } from "crypto";
import { mainHandler } from "@/utils";

import { type NextApiRequest, type NextApiResponse } from "next";

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  return mainHandler(req, res, {
    GET,
    POST: GET,
  });
}
export async function GET(req: NextApiRequest, res: NextApiResponse) {
  try {
    const { address, secret = "secret" } = req.query as {
      address: string;
      secret: string;
    };
    if (!address) {
      res.status(400).json({
        data: null,
        message: '"address" is required',
      });
    }

    const signature = generateSHA512(address + secret);
    res.status(200).json({
      data: signature,
      success: true,
      message: "Signature retrieved successfully",
    });
  } catch (error) {
    res.status(500).json({ error, message: "Something went wrong..." });
  }
}
function generateSHA512(input: string) {
  return createHash("sha512").update(input).digest("hex");
}
