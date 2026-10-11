// SPDX-License-Identifier: MIT
pragma solidity ^0.4.24;

contract ManagedAccount{

    function payOut(address _recipient, uint _amount) returns (bool) {
        if (_recipient.call.value(_amount)()) {
            return true;
        } else {
            return false;
        }
    }
}
