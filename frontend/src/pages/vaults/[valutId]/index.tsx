import { DepositOrWithdrawalBox } from "@/components/DepositOrWithdrawalBox";

export default function VaultPage() {
  return (
    <>
      <DepositOrWithdrawalBox walletBalance={100} walletToken={"SOL"} />
    </>
  );
}
