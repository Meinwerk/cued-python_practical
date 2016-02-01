# TSBteledbase.txt
new = open("new.txt","w")
with open("TSBteledbase.txt","r") as f:
    for line in f:
        new.write(line)
        if "id(" in line:
            new.write('type("television")\n')

new.close()
