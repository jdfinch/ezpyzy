
class StateMachine:
    def __init__(self):
        self.component = self.start()
        self.state = next(self.component)
        self.result = {}

    def __call__(self, *x):
        for y in x:
            self.state = self.component.send(y)

    def start(self):
        x = yield 'start'
        while True:
            if not x.isalnum():
                break
            x = yield 'main text'




if __name__ == '__main__':

    m = StateMachine()

    for x in 'This is a test sentence (it has a (tricky) parenthetical!), can you parse it?':
        m(x)
        print(m.state, m.component)