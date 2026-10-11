// SPDX-License-Identifier: MIT
pragma solidity ^0.4.24;

contract Forwarder {

    address public parentAddress;

    function flush() {
        if (!parentAddress.call.value(this.balance)()) throw;
    }
}
