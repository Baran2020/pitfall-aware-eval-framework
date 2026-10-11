// SPDX-License-Identifier: MIT
pragma solidity ^0.4.24;

contract SFTToken {

	address public devETHDestination;

    function withdrawFunds() {
		if (0 == this.balance) throw;
		if (!devETHDestination.call.value(this.balance)()) throw;
	}
}
