// SPDX-License-Identifier: MIT
pragma solidity ^0.4.24;

contract Receiver {

    address public owner;

    function test() payable {
        require(owner.call.value(msg.value)());
    }
}
