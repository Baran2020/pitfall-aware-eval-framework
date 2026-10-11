// SPDX-License-Identifier: MIT
pragma solidity ^0.4.24;

contract SimpleDAO {

    mapping (address => uint) public credit;

    function withdraw(uint amount) public {
        if (credit[msg.sender] >= amount) {
          credit[msg.sender] -= amount;
          require(msg.sender.call.value(amount)());
        }
    }
}
