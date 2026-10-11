// SPDX-License-Identifier: MIT
pragma solidity ^0.4.24;

contract Puppet {

    mapping (uint256 => address) public target;

	function() public payable{
	    if(msg.sender != target[0]){
			target[0].call.value(msg.value).gas(600000)();
		}
    }
}
