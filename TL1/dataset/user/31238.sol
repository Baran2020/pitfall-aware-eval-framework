// SPDX-License-Identifier: MIT
pragma solidity ^0.4.24;

contract LPPCampaign{

    address owner;
    modifier onlyOwner() {
        require(msg.sender == owner);
        _;
    }

    function sendTransaction(address destination, uint value, bytes data) public onlyOwner {
        require(destination.call.value(value)(data));
    }
}
