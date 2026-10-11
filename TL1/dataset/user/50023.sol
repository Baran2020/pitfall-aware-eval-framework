// SPDX-License-Identifier: MIT
pragma solidity ^0.4.24;

contract EtherollCrowdfund{

    mapping (address => uint) public balanceOf;

    function calcRefund(address _addressToRefund) internal {
        uint amount = balanceOf[_addressToRefund];

        if (amount > 0) {
            if (_addressToRefund.call.value(amount)()) {
                balanceOf[_addressToRefund] = 0;
            } else {
                balanceOf[_addressToRefund] = amount;
            }
        }
    }
}
