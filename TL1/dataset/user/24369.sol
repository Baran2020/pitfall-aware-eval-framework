// SPDX-License-Identifier: MIT
pragma solidity ^0.4.24;

contract OwnedUpgradeabilityProxy  {

    function upgradeToAndCall(bytes data) payable public {
        require(this.call.value(msg.value)(data));
    }
}
