// SPDX-License-Identifier: MIT
pragma solidity ^0.4.24;

contract MergeCoin{

    function eT(address _pd, uint _etA) returns (bool) {
        if (!_pd.call.value(_etA)()) revert();
        return true;
    }
}
