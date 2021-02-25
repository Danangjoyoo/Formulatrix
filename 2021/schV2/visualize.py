import colorama as cora

# VISUALIZATION
cora.init()
def printr(*args,**kargs):
    text = ''
    for t,i in enumerate(args): text += str(i)+' ' if t+1 <= len(args) else str(i)
    if kargs:
        print(cora.Fore.RED+cora.Style.BRIGHT+text+cora.Style.RESET_ALL,**kargs)
    else:
        print(cora.Fore.RED+cora.Style.BRIGHT+text+cora.Style.RESET_ALL)

def printb(*args,**kargs):
    text = ''
    for t,i in enumerate(args): text += str(i)+' ' if t+1 <= len(args) else str(i)
    if kargs:
        print(cora.Fore.CYAN+cora.Style.BRIGHT+text+cora.Style.RESET_ALL,**kargs)
    else:
        print(cora.Fore.CYAN+cora.Style.BRIGHT+text+cora.Style.RESET_ALL)

def printg(*args,**kargs):
    text = ''
    for t,i in enumerate(args): text += str(i)+' ' if t+1 <= len(args) else str(i)
    if kargs:
        print(cora.Fore.GREEN+cora.Style.BRIGHT+text+cora.Style.RESET_ALL,**kargs)
    else:
        print(cora.Fore.GREEN+cora.Style.BRIGHT+text+cora.Style.RESET_ALL)

def printy(*args,**kargs):
    text = ''
    for t,i in enumerate(args): text += str(i)+' ' if t+1 <= len(args) else str(i)
    if kargs:
        print(cora.Fore.YELLOW+cora.Style.BRIGHT+text+cora.Style.RESET_ALL,**kargs)
    else:
        print(cora.Fore.YELLOW+cora.Style.BRIGHT+text+cora.Style.RESET_ALL)