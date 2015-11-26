
class Commands(dict):
    def __init__(self, lst):
        import importlib
        for cmd in lst:
            mod = importlib.import_module(cmd)
            name = getattr(mod, '__name__', cmd).split('.')[-1]
            doc = getattr(mod, '__doc__', "")
            options = getattr(mod, 'options', None)
            funct = getattr(mod, 'execute', None)
            if funct:
                self[name] = (doc, options, funct)

    def help(self, name):
        if name in self:
            print self[name][0]

    def parse(self, parser):
        commands = parser.add_subparsers(title='Available Command', help="Available commands", dest='command')
        for key, cmd in self.items():
            subparser = commands.add_parser(key, help=cmd[2].__doc__)
            if cmd[1]:
                cmd[1](subparser)

