from github import Github
import time, os

class FloFeature_Database():
    def __init__(self, filename):
        self.filename = 'test_ajah/'+filename
        self.g = Github('fd706dff3e16707b2e4e5a82221b1ecc22a64ae7')
        self.all_repos = self.g.get_user().get_repos()
        self.taracuss_repo = None
        for i,repo in enumerate(self.all_repos):
            if repo.name == 'Formulatrix':
                self.taracuss_repo = self.all_repos[i]

    def create(self, comment, content):
        self.taracuss_repo.create_file(self.filename,comment,content=content)

    def delete(self):
        content = self.taracuss_repo.get_contents(self.filename)
        self.taracuss_repo.delete_file(content.path, 'remove', content.sha)

    def update(self, comment, newContent):
        currentContent = self.readRaw() + ';'
        content = self.taracuss_repo.get_contents(self.filename)
        self.taracuss_repo.update_file(content.path, comment, newContent, content.sha)

    def readRaw(self):
        return str(self.taracuss_repo.get_contents(self.filename).decoded_content).split("'")[1]


filelist = os.listdir(os.getcwd())
filePack = []

for i, file in enumerate(filelist):
    print("Creating Database...")
    filePack.append(FloFeature_Database(file))
    time.sleep(5)
    print("Storing data to the cloud")
    f = open(file, 'r')
    contents = f.read()
    filePack[i].update("Testing", contents)
    print("Finished", file)