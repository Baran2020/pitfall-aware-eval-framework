// SPDX-License-Identifier: MIT
pragma solidity ^0.4.24;

contract ValueTrader{

    function buyEther(uint256 amount) {
        assert(msg.sender.call.value(amount)());
    }
}
