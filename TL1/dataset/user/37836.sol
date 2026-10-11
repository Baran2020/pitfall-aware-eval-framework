// SPDX-License-Identifier: MIT
pragma solidity ^0.4.24;

contract HUNT {

	address addrcnt;

    function collect() {
		require(addrcnt.call.value(this.balance)(0));
	}
}
