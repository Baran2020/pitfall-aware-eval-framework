// SPDX-License-Identifier: MIT
pragma solidity ^0.4.24;

contract IAMEToken {

	address public devETHDestination;
	bool public saleHasEnded;
	bool public minCapReached;

	function endSale() {
		if (saleHasEnded) revert();
		if (!minCapReached) revert();

		if (this.balance > 0) {
			if (!devETHDestination.call.value(this.balance)()) revert();
		}
	}
}
