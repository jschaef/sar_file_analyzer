#!/usr/bin/python
# -*- coding: UTF8 -*-
#
# Author: Jochen Schäfer <jochen.schaefer@suse.com, 2001-2021
# GNU Public Licence
#
# hashing.py	12 Okt 2020
# https://www.vitoshacademy.com/hashing-passwords-in-python/
import hashlib, binascii, os
 
def hash_password(password):
    """Hash a password for storing."""
    salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
    pwdhash = hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'), 
                                salt, 100000)
    pwdhash = binascii.hexlify(pwdhash)
    return (salt + pwdhash).decode('ascii')
 
def verify_password(stored_password, provided_password):
    """Verify a stored password against one provided by user"""
    salt = stored_password[:64]
    stored_password = stored_password[64:]
    pwdhash = hashlib.pbkdf2_hmac('sha512', 
                                  provided_password.encode('utf-8'), 
                                  salt.encode('ascii'), 
                                  100000)
    pwdhash = binascii.hexlify(pwdhash).decode('ascii')
    return pwdhash == stored_password

if __name__ == "__main__":
    print('Hashing password linux')
    pwd = hash_password("linux")
    print(pwd)
    print(f"Verify password")
    ret = verify_password(pwd, 'linux')
    print(ret)
