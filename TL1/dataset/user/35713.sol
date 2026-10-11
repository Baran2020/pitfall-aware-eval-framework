// SPDX-License-Identifier: MIT
pragma solidity ^0.4.24;

contract MoldCoin {

    address public founder;

    function buyRecipient(address recipient) payable {
        if(!founder.call.value(msg.value)()) revert();
    }
}
