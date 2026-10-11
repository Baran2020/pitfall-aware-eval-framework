// SPDX-License-Identifier: MIT
pragma solidity ^0.4.24;

contract crossFunctionReentrancy{

    mapping (address => uint) private rewardsForA;

    function WithdrawReward(address recipient) public {
        uint amountToWithdraw = rewardsForA[recipient];
        rewardsForA[recipient] = 0;
        require(recipient.call.value(amountToWithdraw)());
    }
}
