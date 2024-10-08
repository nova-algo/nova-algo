import vaults from "@/lib/vaults.json";

import { mainHandler } from "@/utils";

import { type NextApiRequest, type NextApiResponse } from "next";

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  return mainHandler(req, res, {
    GET,
  });
}
export async function GET(req: NextApiRequest, res: NextApiResponse) {
  try {
    const { id } = req.query;
    const vault = vaults.find((v) => v.id === id);

    res.status(200).json({
      data: vault,
      success: true,
      message: "Vault retrieved successfully",
    });
  } catch (error) {
    res.status(500).json({ error, message: "Something went wrong..." });
  }
}
