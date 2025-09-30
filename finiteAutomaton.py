import sys

class CompExc(Exception):
    def __init__(self, tk: str | list, ln: str | int, ex: str | None = None, subj: str = "token"):
        if isinstance(tk, list):
            tk = " ".join(tk)
        Exception.__init__(self, f"Unexpected {subj} `{tk}` found on line {ln}." + ("" if ex == None else f" Did you mean `{ex}`?"))

class ReExc(Exception):
    def __init__(self, tk: str, ln: str | int):
        Exception.__init__(self, f"State `{tk}` has already been defined, but is being redefined on line {ln}.")

class Tape:
    def __init__(self, tokens: list) -> None:
        self.tokens = tuple(x.strip() for x in tokens)
        self.index = 0
    def __getitem__(self, x) -> str:
        return self.tokens[x]
    def next(self) -> str:
        val: str = self.tokens[self.index]
        self.index += 1
        return val
    def has_next(self) -> bool:
        return self.index < len(self.tokens)
    def reset(self, x) -> None:
        self.index = x
    def __repr__(self) -> str:
        return f"tape@{self.index}: {self.tokens}"

class Automaton:
    def __init__(self, alphabet: list, states: list, initialstate: str, finalstates: list, delta: dict) -> None:
        self.alphabet: list = alphabet
        self.states: list = states
        self.initialstate: str = initialstate
        self.finalstates: list = finalstates
        self.delta: dict = delta
        self.state: str = initialstate
    def process(self, a: str) -> str:
        self.state = self.delta[self.state][a]
        return self.state
    def __repr__(self) -> str:
        return f"auto.alphabet:\n\t{self.alphabet}\nauto.states:\n\t{self.states}\nauto.initialstate:\n\t{self.initialstate}\nauto.finalstates:\n\t{self.finalstates}\nauto.delta:\n\t{self.delta}"
    def construct(lines: list):
        autodict: dict = {
            "alphabet": [],
            "states": [],
            "initialstate": "",
            "finalstates": [],
            "delta": {}
        }
        lines = [x.strip() for x in lines]
        line_num: int = 0
        scope: str = "global"
        c_state: str = ""
        for line in lines:
            line_num += 1
            if line.isspace() or line == "":
                continue
            splits: list = line.split()
            if scope == "global":
                match splits:
                    case ["append", loc, data]:
                        if loc not in ["alphabet", "states", "finalstates"]:
                            raise CompExc(loc, line_num)
                        autodict[loc].append(data)
                    case ["set", loc, data]:
                        if loc not in ["initialstate"]:
                            raise CompExc(loc, line_num)
                        autodict[loc] = data
                    case ["define", loc]:
                        if loc not in ["delta"]:
                            raise CompExc(loc, line_num, ex="delta")
                        scope = "delta"
                    case _:
                        raise CompExc(splits, line_num, subj="command")
            elif scope == "delta":
                match splits:
                    case ["define", loc, state]:
                        if loc not in ["state"]:
                            raise CompExc(loc, line_num, ex="state")
                        if state in autodict["delta"]:
                            raise ReExc(state, line_num)
                        autodict["delta"][state] = {}
                        c_state = state
                        scope = "state"
                    case ["end", loc]:
                        if loc != "delta":
                            raise CompExc(loc, line_num, ex="delta")
                        scope = "global"
                    case _:
                        raise CompExc(splits, line_num, subj="command")
            elif scope == "state":
                match splits:
                    case ["if", "input", inp, "then", "set", "state", state]:
                        autodict["delta"][c_state][inp] = state
                    case ["end", loc]:
                        if loc != "state":
                            raise CompExc(loc, line_num, ex="state")
                        scope = "delta"
                    case _:
                        raise CompExc(splits, line_num, subj="command")
        return Automaton(**autodict)

def main(lines: list, tape: Tape) -> None:
    auto: Automaton = Automaton.construct(lines)
    while tape.has_next():
        auto.process(tape.next())
    print(auto.state)
    print(f"State is in finalstates: {auto.state in auto.finalstates}")

if __name__ == "__main__":
    args: list = sys.argv[1:]
    if len(args) < 1:
        print("Use -h or --help for help.")
        exit(0)
    match args[0]:
        case "-h" | "--help":
            print(
                "Finite Automaton Runtime.\n\n",
                "-h\tThis help menu\n",
                "--help\tThis help menu\n",
                "--formats\tA description of acceptable file formats.\n",
                "-fd <autofile>\tDisplays an automaton from a file containing an automaton description.\n",
                "-fr <autofile> <tapefile>\tRuns an automaton from a file on a tape in a different file."
            )
            exit(0)
        case "--formats":
            print(
                "Formats\n\n"
                "Example of <autofile> format:\n"
                "`\nappend alphabet 0\nappend alphabet 1\nappend states q1\nappend states q2\nappend states q3\nappend states q4\n"
                "set initialstate q1\nappend finalstates q2\nappend finalstates q3\nappend finalstates q4\n\ndefine delta\n    define state q1\n"
                "        if input 1 then set state q2\n        if input 0 then set state q4\n    end state\n\n    define state q2\n        "
                "if input 1 then set state q2\n        if input 0 then set state q3\n    end state\n\n    define state q3\n        if input 1 then "
                "set state q2\n        if input 0 then set state q3\n    end state\n\n    define state q4\n        if input 1 then set state q4\n    "
                "    if input 0 then set state q4\n    end state\nend delta\n`\n\n"
                "Example of <tapefile> format (example corresponds to autofile example):\n`1 0 1 1 0`\n\n"
                "These examples together will give the resulting state of `q3`, due to the tape starting with 1 and ending with 0."
            )
            exit(0)
        case "-fd":
            lines: list = None
            with open(args[1], "r") as file:
                lines = file.readlines()
            print(Automaton.construct(lines))
        case "-fr":
            autolines: list = None
            tapestr: list = None
            with open(args[1], "r") as file:
                autolines = file.readlines()
            with open(args[2], "r") as file:
                tapestr = file.read()
            main(autolines, Tape(tapestr.split()))
        case _:
            print("Use -h or --help for help.")
