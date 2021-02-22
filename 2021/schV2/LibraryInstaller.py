import os, sys, pkg_resources

moduleList =[
			"numpy",
			"matplotlib",
			"pyqtgraph",
			"pyqt5",
			"pandas",
			"keyboard",
			"colorama",
			"tabulate",
			"pyreadline",
			"pyparsing",
			"pyutils",
			"pythonnet",
			"pygithub"
			]

def tryImport(moduleName,tryNo=0):
	if tryNo == 0:
		if not tryImport(moduleName,1):
			tryImport(moduleName, 2)
	elif tryNo == 1:
			packs = [i.key for i in pkg_resources.working_set]
			if moduleName in packs:
				return True
			else:
				return False
	elif tryNo == 2:
		print(f"Installing {moduleName}")
		try: 
			os.system(f"pip3 install {moduleName}")
		except:
			os.system(f"python3 -m pip install {moduleName}")

print("Checking Required Library for Single Channel V2...")
for module in moduleList: tryImport(module)
print("Library Checking Finished..")