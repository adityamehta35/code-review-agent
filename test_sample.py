import os
import sys
import requests  # unused import

password = "hardcoded_secret_123"  # security issue

def calculate(x,y):
    result = x+y
    result2 = x-y
    result3 = x*y
    result4 = x/y  # potential division by zero
    return result

def unused_function():
    pass

for i in range(1000):
    for j in range(1000):
        print(i+j)  # performance issue
