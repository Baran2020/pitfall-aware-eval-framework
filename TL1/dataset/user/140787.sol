// SPDX-License-Identifier: MIT
pragma solidity ^0.4.24;

contract dumbDAO {

    mapping (address => uint) public balances;

    address owner;
    modifier onlyOwner() {
        require(msg.sender == owner);
        _;
    }

    function withdraw(address _recipient) onlyOwner returns (bool) {
        if (balances[msg.sender] == 0){ throw; }

        if (_recipient.call.value(balances[msg.sender])()) {
            balances[msg.sender] = 0;
            return true;
        }
    }
}
