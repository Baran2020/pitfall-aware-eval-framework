// SPDX-License-Identifier: MIT
pragma solidity ^0.4.24;

contract TransferableMultsig {

    function execute(address destination, uint value, bytes data) external {
        require(destination.call.value(value)(data));
    }
}
