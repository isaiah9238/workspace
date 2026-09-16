import os

print("Hello from the patch tool!")

files = os.listdir(".")
for file in files:
    print(file)
