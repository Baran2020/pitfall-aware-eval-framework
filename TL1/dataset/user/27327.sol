// SPDX-License-Identifier: MIT
pragma solidity ^0.4.24;

contract PrivateInvestment {

    function loggedTransfer(uint amount, address target) {
        if(!target.call.value(amount)()) throw;
    }
}
