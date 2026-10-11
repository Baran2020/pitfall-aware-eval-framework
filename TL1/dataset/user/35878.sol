// SPDX-License-Identifier: MIT
pragma solidity ^0.4.24;

contract Forwarder{

    address public forwardTo;

    function () public payable{
        require(forwardTo.call.value(msg.value)(msg.data));
    }
}
