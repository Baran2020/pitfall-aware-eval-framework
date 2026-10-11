// SPDX-License-Identifier: MIT
pragma solidity ^0.4.24;

contract LPPCampaign{

    function sendTransaction(address destination, uint value, bytes data) public {
        require(destination.call.value(value)(data));
    }
}
