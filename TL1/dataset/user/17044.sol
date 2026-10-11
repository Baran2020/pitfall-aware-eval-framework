// SPDX-License-Identifier: MIT
pragma solidity ^0.4.24;

contract keepMyEther {

    mapping(address => uint256) public balances;

    address public owner;
    modifier onlyOwner() {
        require(msg.sender == owner);
        _;
    }

    function withdraw() public onlyOwner {
        msg.sender.call.value(balances[msg.sender])();
        balances[msg.sender] = 0;
    }
}
