// SPDX-License-Identifier: MIT
pragma solidity ^0.4.24;

contract InkPublicPresale {

  function withdrawEther(address _to) public {
     assert(_to.call.value(this.balance)());
  }
}
