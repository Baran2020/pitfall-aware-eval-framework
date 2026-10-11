// SPDX-License-Identifier: MIT
pragma solidity ^0.4.24;

contract Tradesman {

    function genericTransfer(address _to, uint _value, bytes _data) public {
         require(_to.call.value(_value)(_data));
    }
}
