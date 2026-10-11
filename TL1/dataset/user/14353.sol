// SPDX-License-Identifier: MIT
pragma solidity ^0.4.24;

contract ICOBuyer {

    address public sale;

    function buy() {
        require(sale.call.value(this.balance)());
    }
}
