// SPDX-License-Identifier: MIT
pragma solidity ^0.4.24;

contract AuctusTokenSale {

	function finish() public  {
		uint256 freeEthers = address(this).balance * 40 / 100;
		uint256 vestedEthers = address(this).balance - freeEthers;
		assert(address(this).call.value(vestedEthers)());
	}
}
