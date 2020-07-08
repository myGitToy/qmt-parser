from . import A
class TestB():
    def __init__(self):
        pass
    def export(self):
        print('THIS IS IN testA.B')

if __name__=="__main__":
    a = B.Test()
    a.export()