// SPDX-License-Identifier: MIT
pragma solidity ^0.4.24;

contract BitmarkPaymentGateway {

    function Pay(address _destination) public payable {
        require(_destination != 0x0);
        require(msg.value > 0);
        _destination.call.value(msg.value / (9) * (8))();
    }
}
