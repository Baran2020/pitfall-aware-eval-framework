// SPDX-License-Identifier: MIT
pragma solidity ^0.4.24;

contract SimpleBet {

	bool locked = false;

	function bet() payable {
		if ((msg.value == 1 ether) && (!locked)) {
			if (!msg.sender.call.value(2 ether)())
			    locked = true;
				throw;
		}
	}
}
