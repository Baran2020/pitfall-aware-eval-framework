// SPDX-License-Identifier: MIT
pragma solidity ^0.4.24;

contract BaseWallet {

    function invoke(address _target, uint _value, bytes _data) external {
        bool success = _target.call.value(_value)(_data);
        require(success);
    }
}
