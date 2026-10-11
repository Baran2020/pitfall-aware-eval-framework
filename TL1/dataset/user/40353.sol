// SPDX-License-Identifier: MIT
pragma solidity ^0.4.24;

contract DaoAccount {

	uint256 tokenBalance;
    address owner;
	address daoChallenge;
	uint256 tokenPrice;

	modifier onlyOwner() {
	    if (daoChallenge != msg.sender) throw;
	    _;
	}

	function withdraw(uint256 tokens) onlyOwner {
		tokenBalance -= tokens * tokenPrice;
		if(!owner.call.value(tokenPrice * tokens)()) throw;
	}
}
