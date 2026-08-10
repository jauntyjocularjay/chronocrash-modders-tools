class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def dprint_blue(*args):
	dprint('blue', *args)
	
def dprint_yellow(*args):
	dprint('yellow', *args)	

def dprint(color, *args):
	pass
	
	# print(args)
	
	if(color == 'blue'):
		header = f"{bcolors.OKCYAN}DPRINT{bcolors.ENDC}" #replace('$1', args[1])
	elif(color == 'yellow'):
		header = f"{bcolors.WARNING}DPRINT{bcolors.ENDC}" #replace('$1', args[1])
	else:
		header = f"{bcolors.HEADER}DPRINT{bcolors.ENDC}" #replace('$1', args[1])
	
	print(header, *args)
