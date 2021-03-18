import colorama as cora

# VISUALIZATION
cora.init()

def consoleColoring(*args, **kargs):
	args = list(args)
	color = args.pop(0)
	text = ''
	for t,i in enumerate(args): text += str(i)+' ' if t+1 < len(args) else str(i)
	if kargs:
		print(color+cora.Style.BRIGHT+text+cora.Style.RESET_ALL,**kargs)
	else:
		print(color+cora.Style.BRIGHT+text+cora.Style.RESET_ALL)

def printr(*args,**kargs): # Red Font
	args = list(args)
	args.insert(0, cora.Fore.RED)
	consoleColoring(*args,**kargs)

def printbr(*args,**kargs): # Red Background
	args = list(args)
	args.insert(0, cora.Back.RED)
	consoleColoring(*args,**kargs)

def printb(*args,**kargs): # Light Blue Font
	args = list(args)
	args.insert(0, cora.Fore.CYAN)
	consoleColoring(*args,**kargs)

def printbb(*args,**kargs): # Light Blue Background
	args = list(args)
	args.insert(0, cora.Back.CYAN)
	consoleColoring(*args,**kargs)

def printdb(*args,**kargs): # Dark Blue Font
	args = list(args)
	args.insert(0, cora.Fore.BLUE)
	consoleColoring(*args,**kargs)

def printbdb(*args,**kargs): # Dark Blue Background
	args = list(args)
	args.insert(0, cora.Back.BLUE)
	consoleColoring(*args,**kargs)

def printg(*args,**kargs): # Green Font
	args = list(args)
	args.insert(0, cora.Fore.GREEN)
	consoleColoring(*args,**kargs)

def printbg(*args,**kargs): # Green Background
	args = list(args)
	args.insert(0, cora.Back.GREEN)
	consoleColoring(*args,**kargs)
	
def printy(*args,**kargs): # Yellow Font
	args = list(args)
	args.insert(0, cora.Fore.YELLOW)
	consoleColoring(*args,**kargs)

def printby(*args,**kargs): # Yellow Background
	args = list(args)
	args.insert(0, cora.Back.YELLOW)
	consoleColoring(*args,**kargs)

def printm(*args,**kargs): # Magenta Font
	args = list(args)
	args.insert(0, cora.Fore.MAGENTA)
	consoleColoring(*args,**kargs)

def printbm(*args,**kargs): # Magenta Background
	args = list(args)
	args.insert(0, cora.Back.MAGENTA)
	consoleColoring(*args,**kargs)

def printbw(*args,**kargs): # White Background
	args = list(args)
	args.insert(0, cora.Back.WHITE+cora.Fore.BLACK)
	consoleColoring(*args,**kargs)