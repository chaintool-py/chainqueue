
class Adapter:

    def __init__(self, backend):
        self.backend = backend


    def process(self, chain_spec):
        raise NotImplementedEror()


    def add(self, chain_spec, bytecode):
        raise NotImplementedEror()
