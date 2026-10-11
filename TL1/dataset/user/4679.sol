// SPDX-License-Identifier: MIT
pragma solidity ^0.4.24;

contract TokedoDaico {

    address public milestoneSystem;

    function forwardEther() payable public returns(bool) {
        require(milestoneSystem.call.value(msg.value)());
        return true;
    }
}
