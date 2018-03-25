import inspect

from prompt_toolkit import prompt
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.contrib.completers import WordCompleter
from prompt_toolkit.completion import Completer, Completion


def print_args(sig):
    arguments = list(sig.parameters.keys())
    s = "("
    for a in arguments[1:]:
        s += ", " if len(s) > 1 else ""
        s += str(sig.parameters[a])
    s += ")"
    return s


def get_methods(class_name):
    return [func for func in dir(class_name) if callable(getattr(class_name, func)) and not func.startswith("__")]


def print_class_methods(class_name):
    for func in get_methods(class_name):
        sig = inspect.signature(getattr(class_name, func))
        print("{command} {args}".format(command=func, args=print_args(sig)))


class PublicKey:
    pass


class WalletApi:
    def create_account(self,
                       creator: str,
                       new_name: str,
                       json_meta: str,
                       owner_key,
                       active_key,
                       posting_key,
                       memo_key,
                       broadcast: bool):
        pass


class Impl:
    def __init__(self):
        self.run = True
        self.prompt_message = "new"

    def __dummy__(self):
        pass

    def help(self):
        print_class_methods(Impl)
        print_class_methods(WalletApi)

    def exit(self):
        self.run = False

    def unlock(self):
        password = prompt("enter password: ", is_password=True)
        self.prompt_message = "unlocked"

    def lock(self):
        self.prompt_message = "locked"

    def set_password(self):
        password = prompt("enter password: ", is_password=True)
        self.prompt_message = "locked"


class MyCustomCompleter(Completer):
    def __init__(self, complition):
        self.completion = complition

        self.wallet = get_methods(WalletApi)
        self.app = get_methods(Impl)


    def get_completions(self, document, _):
        x = document.text
        word_before_cursor = document.get_word_before_cursor(WORD=True)

        # print(word_before_cursor)
        yield Completion('x', start_position=0)
        yield Completion('y', start_position=0)


class App:
    def __init__(self):
        self.impl = Impl()
        self.wallet = WalletApi()

        self.history = InMemoryHistory()
        # self.completer = WordCompleter(self.get_commands())
        self.completer = MyCustomCompleter(self.get_commands())

    def get_commands(self):
        method_list = []
        method_list += get_methods(WalletApi)
        method_list += get_methods(Impl)

        return method_list

    def prompt(self):
        line = prompt(self.impl.prompt_message + ' > ', completer=self.completer, history=self.history)
        return line

    def get_command(self, line):
        words = line.split()

        if len(words) > 0:
            return (words[0], words[1:])
        else:
            return ("__dummy__", [])

    def run(self):
        while self.impl.run:
            line = self.prompt()

            command, args = self.get_command(line)

            try:
                getattr(self.impl, command)(*args)
                continue
            except AttributeError as e:
                pass
                # print("error: %s" % e)

            try:
                getattr(self.wallet, command)(*args)
            except AttributeError as e:
                print("error: %s" % e)
            except TypeError as e:
                print("error: %s" % e)


def main():
    app = App()
    app.run()


def tests_signature():
    sig = inspect.signature(getattr(WalletApi, "create_account"))

    assert print_args(sig) == "(creator:str, " \
                              "new_name:str, " \
                              "json_meta:str, " \
                              "owner_key:wallet.PublicKey, " \
                              "active_key:wallet.PublicKey, " \
                              "posting_key:wallet.PublicKey, " \
                              "memo_key:wallet.PublicKey, " \
                              "broadcast:bool)"
