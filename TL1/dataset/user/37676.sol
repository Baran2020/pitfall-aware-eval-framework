// SPDX-License-Identifier: MIT
pragma solidity ^0.4.24;

contract DeadMansSwitch {

	function send(address _to, uint _value, bytes _data) {
		if (!_to.call.value(_value)(_data)) throw;
	}
}
