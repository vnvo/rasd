class Command(object):
    name = ""
    
    def execute(self, *args):
        raise NotImplementedError
    
    
    
class Status(Command):
    name = "status"
    
    def execute(self, *args):
        pass
