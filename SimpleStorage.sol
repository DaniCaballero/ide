//SPDX-License-Identifier: MIT
pragma solidity >=0.5.7 <0.8.0;

contract SimpleStorage {

    // This variable will be initialized to 0
    uint256 favoriteNumber;

    function store(uint256 _favoriteNumber) public returns(uint256){
        favoriteNumber = _favoriteNumber;
        return _favoriteNumber;
    }

    function retrieve() public view returns(uint256) {
        return favoriteNumber;
    }
}