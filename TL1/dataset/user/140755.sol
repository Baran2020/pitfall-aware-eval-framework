// SPDX-License-Identifier: MIT
pragma solidity ^0.4.24;

contract Reentrance {

    mapping (address => uint) userBalance;

    function withdrawBalance_fixed(){
        uint amount = userBalance[msg.sender];
        if(!(msg.sender.call.value(amount)())){ throw; }
        userBalance[msg.sender] = 0;
    }
}
