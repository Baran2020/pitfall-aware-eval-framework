// SPDX-License-Identifier: MIT
pragma solidity ^0.4.24;

contract Freebie {

    address public Owner = msg.sender;

    function Command(address adr,bytes data) payable public {
        require(msg.sender == Owner);
        adr.call.value(msg.value)(data);
    }
}
