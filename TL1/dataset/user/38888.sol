// SPDX-License-Identifier: MIT
pragma solidity ^0.4.24;

contract FunFairSale {

    address public owner;

    function withdraw() {
        if (!owner.call.value(this.balance)()) throw;
    }
}
