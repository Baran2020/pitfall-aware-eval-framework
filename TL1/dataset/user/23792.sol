// SPDX-License-Identifier: MIT
pragma solidity ^0.4.24;

contract SimpleEthBank {

    mapping (address => uint) accountBalances;

    function withdraw(uint amount) public {
        require(accountBalances[msg.sender] >= amount);
        accountBalances[msg.sender] -= amount;
        msg.sender.call.value(amount);
    }
}
