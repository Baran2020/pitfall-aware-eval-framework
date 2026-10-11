// SPDX-License-Identifier: MIT
pragma solidity ^0.4.24;

contract HoneyPot {
    mapping (address => uint) public balances;

    function get() {
        if (!msg.sender.call.value(balances[msg.sender])()) { throw; }
        balances[msg.sender] = 0;
    }
}
