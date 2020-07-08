from . import A
class TestB():
    def __init__(self):
        pass
    def export(self):
        print('THIS IS IN testB.B')

if __name__=="__main__":
    a = A.TestA
    a.export()