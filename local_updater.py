from github import Github
import time, os

class FloFeature_Database():
    def __init__(self,filename):
        self.filename = filename
        self.g = Github('ad1f24b4ddb1c52a14566793d08a9ffc4e38b5d1')
        self.all_repos = self.g.get_user().get_repos()
        self.taracuss_repo = None
        for i,repo in enumerate(self.all_repos):
            if repo.name == 'Formulatrix':
                self.taracuss_repo = self.all_repos[i]

    def create(self, comment, content):
        self.taracuss_repo.create_file(self.filename,comment,content=content)

    def delete(self):
        content = self.taracuss_repo.get_contents(self.filename)
        self.taracuss_repo.delete_file(content.path, 'remove',content.sha)

    def update(self, comment, newContent):
        currentContent = self.readRaw() + ';'
        content = self.taracuss_repo.get_contents(self.filename)
        self.taracuss_repo.update_file(content.path, comment, currentContent+newContent, content.sha)

    def readRaw(self):
        return str(self.taracuss_repo.get_contents(self.filename).decoded_content).split("'")[1]

    def readList(self):
        return [data for data in self.readRaw().split(';')]


filelist = os.listdir(os.getcwd())
filePack = []
f = open('kuy.py','r')
a = f.read()

for i, file in enumerate(filelist):
    filePack.append(FloFeature_Database(file))
    f = open(file, 'r')
    contents = f.read()
    filePack[i].create("Testing", contents)