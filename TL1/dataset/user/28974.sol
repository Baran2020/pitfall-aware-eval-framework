// SPDX-License-Identifier: MIT
pragma solidity ^0.4.24;

contract Payee {

    uint256 public price;

    function pay(uint256 count) public payable {
        assert(msg.value >= price * count);
        if(!msg.sender.call.value(msg.value - price * count)()){ revert(); }
    }
}
