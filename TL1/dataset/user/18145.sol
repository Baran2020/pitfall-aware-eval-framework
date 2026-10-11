// SPDX-License-Identifier: MIT
pragma solidity ^0.4.24;

contract CrowdsaleProxy {

    function upgradeToAndCall(address newTarget, bytes data) payable public {
        require(address(this).call.value(msg.value)(data));
    }
}
