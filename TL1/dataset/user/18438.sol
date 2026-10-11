// SPDX-License-Identifier: MIT
pragma solidity ^0.4.24;

contract BoomerangLiquidity {

    address public sk2xContract;

    function donate() payable public {
        require(sk2xContract.call.value(msg.value).gas(1000000)());
    }
}
