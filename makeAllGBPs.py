#!/usr/bin/env python

# Author: github/asanzo
# Creative Commons - Copy and mention us :)
# Version: 1.0.1

import os
import zipfile
import hashlib
import subprocess
import sys

# Complete for each different repository
thisRepo = 'ezeforte/ejerciciosGobstones'
gbpsPath = os.path.join("ArchivosDeProyectos-Generado")

class GBPGenerator:
    currentTime = None
    gbpsUpdated = 0

    def updateAll(self):
        import json
        guides = json.load (open('guides.json'))
        self.createGBPFolder()
        for guide in guides:
            for exercise in guide["exercises"]:
                self.updateGBP(os.path.normpath(exercise["path"]))
        print("Update done. Amount of GBPs updated: " + str(self.gbpsUpdated))

    def updateGBP(self, projectPath):
        # If it doesn't exist a GBP for this project, generate it and return.
        try:
            existinggbpPath = self.findExistingGBP(projectPath)
        except NotFoundError:
            self.logNewGBP("Will generate new GBP", projectPath)
            return
        finally:
            self.generateGBP(projectPath)
        
        # If it actually does exist a previous GBP, discard the newly generated in case it is the same as the existent
        # This way the script only generates GBPs for projects that did change.
        if MD5().equals(existinggbpPath, self.gbpPath(projectPath)):
            os.remove(self.gbpPath(projectPath))
        else:
            # In case the new one has changed, then we can remove the previous one.
            self.logNewGBP("Project changed, GBP updated", projectPath)
            os.remove(existinggbpPath)

    def logNewGBP(self,description, projectPath):
        print(description + ": " + self.gbpPath(projectPath))
        self.gbpsUpdated += 1

    def generateGBP(self,projectPath):
        zipf = zipfile.ZipFile(self.gbpPath(projectPath), 'w', zipfile.ZIP_DEFLATED)
        self.zipdir(projectPath, zipf)
        zipf.close()

    def zipdir(self,path, ziph):
        for root, dirs, files in os.walk(path):
            for file in files:
                realFilepath = os.path.join(root, file)
                ziph.write(realFilepath, os.path.relpath(realFilepath, path))

    def gbpPath(self,projectPath):
        if self.currentTime is None: # One time for all script execution. This way if I call gbpPath twice with same parameter, it returns the same value.
            from time import localtime, strftime
            self.currentTime = strftime("%Y-%m-%d-%H%M%S", localtime())
        
        return os.path.join(self.gbpsPath(),os.path.split(projectPath)[1] + '-' + self.currentTime + '.gbp').encode('utf-8')  

    def deleteAll(self):
        self.createGBPFolder()
        for item in os.listdir(self.gbpsPath()):
            if item.endswith(".gbp"):
                os.remove(os.path.join(self.gbpsPath(), item))

    def gbpsPath(self):
        return gbpsPath

    def findExistingGBP(self,projectPath): # Returns the last generated gbp path (sorts by filename)
        result = []
        for root, dirs, files in os.walk(self.gbpsPath()):
            for name in sorted(files):
                if name.startswith(os.path.split(projectPath)[1].encode('utf8')):
                    result.append(os.path.join(root, name))
        
        if result == []:
            raise NotFoundError("Path not found: " + projectPath)

        return result[-1]
    
    def createGBPFolder(self):
        if not os.path.exists(self.gbpsPath()):
            os.makedirs(self.gbpsPath())

class NotFoundError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class MD5:
    def sum(self,fname):
        hash_md5 = hashlib.md5()
        with open(fname, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def equals(self, fname1, fname2):
        return self.sum(fname1) == self.sum(fname2)
    
def bashRun(cmds):
    print("Running: " + " ".join(cmds))
    process = subprocess.Popen(cmds, stdout=subprocess.PIPE)
    output, error = process.communicate()
    
    if output:
        print(output)
    if process.returncode != 0:
        sys.exit(process.returncode)
    if error:
        print("Error code: " + str(process.returncode) + ". Error Description: " + error.strip())
        sys.exit(process.returncode)

class GBPUploader():
    def checkoutBranch(self):
        bashRun('git remote set-branches --add origin archivosDeProyecto'.split())
        bashRun('git fetch origin'.split())
        bashRun('git checkout archivosDeProyecto'.split())
        bashRun('git merge master'.split())
    def commit(self):
        bashRun('git add .'.split())
        bashRun(['git', 'commit', '--author="Travis CI <travis@travis-ci.org>"', '--message', '"Generated GBPs. Travis build: ' + os.environ['TRAVIS_BUILD_NUMBER'] +'"'])
    def push(self):
        bashRun(('git remote add origin-modify https://' + os.environ['GH_TOKEN'] + '@github.com/' + thisRepo + '.git').split())
        bashRun('git push --quiet --set-upstream origin-modify archivosDeProyecto'.split())

if __name__ == '__main__':
    if len(sys.argv) == 1:
        # GBPGenerator().deleteAll()
        GBPUploader().checkoutBranch()
        GBPGenerator().updateAll()
    elif len(sys.argv) == 2 and sys.argv[1] == 'publishGBPs':
        GBPUploader().commit()
        GBPUploader().push()
    else:
        print("Incorrect use of script.")
        print("Usage:")
        print(" - no arguments: it will update gbps.")
        print(" - argument 'publishGBPs' will commit and push changes to the repository")