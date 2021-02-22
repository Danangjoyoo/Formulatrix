import colorama as cora

# VISUALIZATION
cora.init()
def printr(*args):
    text = ''
    for t,i in enumerate(args): text += str(i)+' ' if t+1 <= len(args) else str(i)
    print(cora.Fore.RED+cora.Style.BRIGHT+text+cora.Style.RESET_ALL)

def printb(*args):
    text = ''
    for t,i in enumerate(args): text += str(i)+' ' if t+1 <= len(args) else str(i)
    print(cora.Fore.CYAN+cora.Style.BRIGHT+text+cora.Style.RESET_ALL)

def printg(*args):
    text = ''
    for t,i in enumerate(args): text += str(i)+' ' if t+1 <= len(args) else str(i)
    print(cora.Fore.GREEN+cora.Style.BRIGHT+text+cora.Style.RESET_ALL)

def printy(*args):
    text = ''
    for t,i in enumerate(args): text += str(i)+' ' if t+1 <= len(args) else str(i)
    print(cora.Fore.YELLOW+cora.Style.BRIGHT+text+cora.Style.RESET_ALL)