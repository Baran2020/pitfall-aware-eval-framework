// SPDX-License-Identifier: MIT
pragma solidity ^0.4.24;

contract PreICOProxyBuyer {

    mapping(address => uint) public balances;
    address investor = msg.sender;

    function refund() {
        if(balances[investor] == 0) throw;
        uint amount = balances[investor];
        balances[investor] = 0;
        if(!(investor.call.value(amount)())) throw;
    }
}
