import inspect
import re

from prompt_toolkit import prompt
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.contrib.completers import WordCompleter
from prompt_toolkit.completion import Completer as BaseCompleter
from prompt_toolkit.completion import Completion as BaseCompletion

from fuzzywuzzy import fuzz
from fuzzywuzzy import process


class ToolBar:
    def __init__(self):
        self.message = "Bar"


bar = ToolBar()


def split_command_and_args(text):
    return text.split()


def print_args(sig: inspect.Signature):
    s = "("
    for k, a in sig.parameters.items():
        if a.name == "self":
            continue

        s += ", " if len(s) > 1 else ""
        s += "%s: %s" % (a.name, a.annotation.__name__)
    s += ")"
    return s


def get_methods(class_name):
    return [func for func in dir(class_name) if callable(getattr(class_name, func)) and not func.startswith("__")]


def get_method_completions(method_signature, completer):
    result = dict()

    for k, v in method_signature.parameters.items():
        try:
            completions = getattr(v.annotation, "completions")
            result[k] = completions(completer)
        except AttributeError:
            pass
    
    return result


def get_methods_with_completions(class_name, completer):
    result = dict()
    methods = get_methods(class_name)

    for m in methods:
        sig = inspect.signature(getattr(class_name, m))

        c = []

        for k, v in sig.parameters.items():
            try:
                callback = getattr(v.annotation, "completions")

                c.append({"arg": v.name, "callback": callback(completer)})
            except AttributeError:
                pass
        
        result[m] = c

    return result


def print_class_methods(class_name):
    for func in get_methods(class_name):
        sig = inspect.signature(getattr(class_name, func))
        print("{command} {args}".format(command=func, args=print_args(sig)))


class PublicKey:
    value = ""

    def __str__(self):
        return self.value

    @staticmethod
    def completions(completer):
        return completer.get_public_keys


class AccountName:
    name = ""

    def __str__(self):
        return self.name

    @staticmethod
    def completions(completer):
        return completer.get_accounts


class WitnessName:
    name = ""

    def __str__(self):
        return self.name

    @staticmethod
    def completions(completer):
        return completer.get_witnesses


class Str:
    value = ""

    def __str__(self):
        return self.value

    @staticmethod
    def completions(completer):
        return completer.get_dummy


class Bool:
    value = False

    def __str__(self):
        return str(self.value)

    def __bool__(self):
        return self.value

    @staticmethod
    def completions(completer):
        return completer.get_bool


class WalletApi:
    def __init__(self, completer):
        self.completer = completer

    def create_account(self,
                       creator: AccountName,
                       new_name: AccountName,
                       json_meta: Str,
                       owner_key: PublicKey,
                       active_key: PublicKey,
                       posting_key: PublicKey,
                       memo_key: PublicKey,
                       broadcast: Bool):

        self.completer.accounts.add(creator)
        self.completer.accounts.add(new_name)

    def update_witness(self,
                       initiator: AccountName,
                       witness: WitnessName,
                       approve: Bool,
                       broadcast: Bool):

        self.completer.accounts.add(initiator)
        self.completer.witnesses.add(witness)

    def vote_for_witness(self,
                         initiator: AccountName,
                         witness: WitnessName,
                         approve: Bool,
                         broadcast: Bool):
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


class Completer:
    def __init__(self):
        self.accounts = set()
        self.witnesses = set()
        self.public_keys = set()

        self.accounts.update(["alex", "joe", "jim", "bob", "hue"])
        self.witnesses.update(["w1", "w2", "w3", "bob", "hue"])
        self.public_keys.update(["SCR5xRhdyDbFRgPTbk8ZrBoFLC95zH2hxFAKSFguf6VFvQuqHhEvi",
                                 "SCR4u8Ee47LQUUVKSwpbTBTSYm5tDnHv8V41rVENxVoYJVzoXVxb8",
                                 "SCR7JrxZ5ikZyvq11CoYzzxuvVgMnkNt9CAJ7BdfD92fRfz2G3SY9"])

    def get_accounts(self):
        return self.accounts

    def get_public_keys(self):
        return self.public_keys

    def get_witnesses(self):
        return self.witnesses

    @staticmethod
    def get_bool():
        return ["true", "false"]

    @staticmethod
    def get_dummy():
        return ['""', "{}"]


class CompleterImpl(BaseCompleter):
    def __init__(self, completions):
        self.commands = []

        self.commands += get_methods(WalletApi)
        self.commands += get_methods(Impl)

        self.completions = completions

    @staticmethod
    def safe_split(text):
        """
        Shlex can't always split. For example, "\" crashes the completer.
        """
        try:
            words = split_command_and_args(text)
            return words
        except:
            return text

    @staticmethod
    def get_tokens(text):
        if text is not None:
            text = text.strip()
            words = CompleterImpl.safe_split(text)
            return words[0], words[1:]
        return "", []

    def get_command_arg_completions(self, command: str, index: int):
        if command not in self.completions:
            return []

        if index >= len(self.completions[command]):
            return []

        return self.completions[command][index]["callback"]()

    def get_completions(self, document, _):
        word_before_cursor = document.get_word_before_cursor(WORD=True)

        command, args = CompleterImpl.get_tokens(document.text)

        in_command = (len(args) > 0) or ((not word_before_cursor) and command)

        if in_command:
            index = len(args) if not word_before_cursor else len(args) - 1
            completions = self.get_command_arg_completions(command, index)
            bar.message = "%s : '%s' '%s'" % (str(index), word_before_cursor, document.text)
        else:
            completions = self.commands
            bar.message = ""

        result = self.fuzzy_search(word_before_cursor, completions)

        for r in result:
            position = 0

            if len(word_before_cursor) > 0:
                position = len(word_before_cursor) * -1

            yield BaseCompletion(r, start_position=position)

    @staticmethod
    def fuzzy_search(word_before_cursor, completions):
        if len(word_before_cursor) == 0:
            return completions

        pattern = re.compile("^[A-Z,a-z,0-9]*$")

        if not pattern.match(word_before_cursor):
            return completions

        completion = []

        result = process.extract(word_before_cursor, completions, limit=5)
        for r in result:
            word, ratio = r
            if ratio > 50:
                completion.append(word)

        if len(completion) == 0:
            return completions

        return completion


class App:
    def __init__(self):
        self.history = InMemoryHistory()
        # self.completer = WordCompleter(self.get_commands())

        completer = Completer()

        self.impl = Impl()
        self.wallet = WalletApi(completer)

        self.completions = {}
        self.completions.update(get_methods_with_completions(WalletApi, completer))
        self.completions.update(get_methods_with_completions(Impl, completer))

        self.completer = CompleterImpl(self.completions)

    def prompt(self):
        def get_title():
            return 'Wallet'

        # from prompt_toolkit.styles import style_from_dict
        from prompt_toolkit.token import Token

        def get_bottom_toolbar_tokens(cli):
            return [(Token.Toolbar, bar.message)]

        line = prompt(self.impl.prompt_message + ' > ',
                      completer=self.completer,
                      history=self.history,
                      get_bottom_toolbar_tokens=get_bottom_toolbar_tokens,
                      get_title=get_title)
        return line

    @staticmethod
    def parse_command(line):
        words = split_command_and_args(line)

        if len(words) > 0:
            return words[0], words[1:]

        return "__dummy__", []

    def run(self):
        while self.impl.run:
            line = self.prompt()

            command, args = self.parse_command(line)

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


def test_get_completions():
    class TestCompleter:
        def get_completions_for_my_type(self):
            return ["x", "y"]

    class MyType:
        value = ""

        def __str__(self):
            return self.value

        @staticmethod
        def completions(completer):
            return completer.get_completions_for_my_type()
  
    class MyApi:
        def foo(self, a: MyType, b: MyType):
            pass

    completer = TestCompleter()
    
    sig = inspect.signature(getattr(MyApi, "foo"))

    assert get_method_completions(sig, completer) == {"a": ["x", "y"], "b": ["x", "y"]}


def test_y():
    class TestCompleter:
        @staticmethod
        def get_completions_for_my_type():
            return ["x", "y"]

    class MyType:
        value = ""

        def __str__(self):
            return self.value

        @staticmethod
        def completions(completer):
            return completer.get_completions_for_my_type
  
    class MyApi:
        def foo(self, a: MyType, b: MyType):
            pass

    completer = TestCompleter()
    
    r = get_methods_with_completions(MyApi, completer)

    assert r["foo"][0]["callback"]() == ["x", "y"]


def test_z():
    completer = Completer()

    completions = {}
    completions.update(get_methods_with_completions(WalletApi, completer))
    completions.update(get_methods_with_completions(Impl, completer))

    print("")
    print(completions)


def test_x():

    def foo():
        return ["q"]

    a = {"create_account": [foo]}

    assert "create_account" in a

    assert a["create_account"][0]() == ["q"]
