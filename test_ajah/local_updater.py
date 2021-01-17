from github import Github
import time, os

class FloFeature_Database():
    def __init__(self, filename):
        self.filename = 'test_ajah/'+filename
        self.g = Github('0bed130be30d056b35305d406e399a54d452115d')
        self.all_repos = self.g.get_user().get_repos()
        self.branchName = 'main'
        self.taracuss_repo = None
        for i,repo in enumerate(self.all_repos):
            if repo.name == 'Formulatrix':
                self.taracuss_repo = self.all_repos[i]

    def create(self, comment, content):
        self.taracuss_repo.create_file(self.filename,comment,content=content,branch=self.branchName)

    def delete(self):
        content = self.taracuss_repo.get_contents(self.filename)
        self.taracuss_repo.delete_file(content.path, 'remove', content.sha ,branch=self.branchName)

    def update(self, comment, newContent):
        content = self.taracuss_repo.get_contents(self.filename)
        self.taracuss_repo.update_file(content.path, comment, newContent, content.sha, branch=self.branchName)

    def readRaw(self):
        return str(self.taracuss_repo.get_contents(self.filename).decoded_content).split("'")[1]


filelist = os.listdir(os.getcwd())
filePack = []

i = 0
while True:
    for i, file in enumerate(filelist):
        print("Creating Database...")
        filePack.append(FloFeature_Database(file))
        #filePack[i].delete()
        print("Storing data to the cloud")
        f = open(file, 'r')
        contents = f.read()
        f.close()
        filePack[i].update("Testing", contents)
        print("Finished", file)
    i += 1
    print(i)