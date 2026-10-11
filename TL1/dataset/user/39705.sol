// SPDX-License-Identifier: MIT
pragma solidity ^0.4.24;

contract FDC {

    address public foundationWallet;

    function empty() returns (bool) {
        return foundationWallet.call.value(this.balance)();
    }
}
