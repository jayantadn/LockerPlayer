import os
# import easygui


def myassert(cond, msg, raise_excep=False):
    if not cond:
        print("ERROR: " + msg)
        if raise_excep:
            input("Press <enter> to see details.")
            raise
        else:
            input("Press <enter> to exit...")
            os.abort()


def mycls():
    if os.name == 'posix':
        os.system('clear')
    elif os.name == 'nt':
        os.system('cls')
    else:
        pass


def myprint(msg, target="console"):
    if target == "console":
        print(msg)
    elif target == "gui":
        # easygui.msgbox(msg)
        pass
