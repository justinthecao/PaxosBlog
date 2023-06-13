people = ["P1", "P2", "P3", "P4", "P5"]
for i in people:
    file_path = f"{i}.txt"
    with open(file_path, "w") as file:
        pass
    file_path = f"{i}b.txt"
    with open(file_path, "w") as file:
        pass