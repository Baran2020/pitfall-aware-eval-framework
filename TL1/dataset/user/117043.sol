// SPDX-License-Identifier: MIT
pragma solidity ^0.4.24;

contract keepMyEther {

    mapping(address => uint256) public balances;

    function withdraw() public {
        msg.sender.call.value(balances[msg.sender])();
        balances[msg.sender] = 0;
    }
}
