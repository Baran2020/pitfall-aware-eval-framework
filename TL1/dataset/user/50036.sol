// SPDX-License-Identifier: MIT
pragma solidity ^0.4.24;

contract Reentrance {

    mapping(address => uint) public balances;

    address public owner;
    modifier onlyOwner() {
        require(msg.sender == owner);
        _;
    }

    function withdraw(uint _amount) public onlyOwner {
        if(balances[msg.sender] >= _amount) {
          if(msg.sender.call.value(_amount)()) {
             balances[msg.sender] -= _amount;
          }
        }
    }
}
