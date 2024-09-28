import React from "react";
import * as web3modal from "@web3modal/solana/react";
import ConnectButton from "./ConnectButton";
const { useWeb3Modal, useWeb3ModalEvents, useWeb3ModalAccount } = web3modal;

type Props = {
  title: string;

  accountCallback: (account: string | null) => void;
};

const WalletConnectModal: React.FC<Props> = ({ title }) => {
  const { open } = useWeb3Modal();
  const s = useWeb3ModalEvents();
  const account = useWeb3ModalAccount();
  console.log(account);
  console.log(s.data.event);
  console.log(s.data.event == "CONNECT_SUCCESS");
  const connect = async () => {
    open();
  };

  return (
    <>
      <w3m-account-button />

      <w3m-button />
      <ConnectButton
        title={title}
        icon={"/icons/wallet_connect.png"}
        callback={connect}
      />
    </>
  );
};

export default WalletConnectModal;
