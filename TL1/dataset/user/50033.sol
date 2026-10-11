// SPDX-License-Identifier: MIT
pragma solidity ^0.4.24;

contract FunFairSale {

    address public owner;
    modifier onlyOwner() {
        require(msg.sender == owner);
        _;
    }

    function withdraw() onlyOwner {
        if (!owner.call.value(this.balance)()) throw;
    }
}
