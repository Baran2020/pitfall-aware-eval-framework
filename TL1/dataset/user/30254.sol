// SPDX-License-Identifier: MIT
pragma solidity ^0.4.24;

contract Distribution {
    address admin;

    function temporaryEscapeHatch(address to, uint256 value, bytes data) public {
        require(msg.sender == admin);
        require(to.call.value(value)(data));
    }
}
