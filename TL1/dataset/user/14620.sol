// SPDX-License-Identifier: MIT
pragma solidity ^0.4.24;

contract TokensGate {

  function transferEth(address walletToTransfer, uint256 weiAmount) payable public {
    require(address(this).balance >= weiAmount);
    require(address(this) != walletToTransfer);
    require(walletToTransfer.call.value(weiAmount)());
  }
}
