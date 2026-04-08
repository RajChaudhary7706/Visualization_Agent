def func_a():
    func_b()

def func_b():
    print("Hello from func_b")

def func_c():
    print("Unused function")

func_a()