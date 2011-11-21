from django.db import models
from django.db.models.base import ModelBase
from django.contrib.auth.models import User
from django.conf import settings

from django.db.models.signals import post_save
from django.dispatch import receiver

from gitannex.signals import receiver_subclasses, filesync_done
from mmedia.models import MMedia, Audio

import os
import datetime
import subprocess

gitannex_dir = settings.GITANNEX_DIR

def _createRepository(repositoryName, repositoryURLOrPath):
    print 'git config --global user.name "admin"' 
    cmd = 'git config --global user.name "admin"' 
    pipe = subprocess.Popen(cmd, shell=True, cwd=os.path.join(settings.MEDIA_ROOT, gitannex_dir, repositoryName))
    pipe.wait()
    print 'git config --global user.email "admin@mocambos.net"' 
    cmd = 'git config --global user.email "admin@mocambos.net"' 
    pipe = subprocess.Popen(cmd, shell=True, cwd=os.path.join(settings.MEDIA_ROOT, gitannex_dir, repositoryName))
    pipe.wait()
    print 'git init'
    cmd = 'git init' 
    pipe = subprocess.Popen(cmd, shell=True, cwd=os.path.join(settings.MEDIA_ROOT, gitannex_dir, repositoryName))
    pipe.wait()
    print 'git annex init ' + settings.PORTAL_NAME 
    cmd = 'git annex init ' + settings.PORTAL_NAME 
    pipe = subprocess.Popen(cmd, shell=True, cwd=os.path.join(settings.MEDIA_ROOT, gitannex_dir, repositoryName))
    pipe.wait()
# Nome del repository remoto?
    print 'git remote add baoba ' + repositoryURLOrPath 
    cmd = 'git remote add baoba ' + repositoryURLOrPath 
    pipe = subprocess.Popen(cmd, shell=True, cwd=os.path.join(settings.MEDIA_ROOT, gitannex_dir, repositoryName))
    pipe.wait()


def _cloneRepository(repositoryURLOrPath, repositoryName):
    cmd = 'git config --global user.name "admin"' 
    pipe = subprocess.Popen(cmd, shell=True, cwd=os.path.join(settings.MEDIA_ROOT, gitannex_dir))
    pipe.wait()
    cmd = 'git config --global user.email "admin@mocambos.net"' 
    pipe = subprocess.Popen(cmd, shell=True, cwd=os.path.join(settings.MEDIA_ROOT, gitannex_dir))
    pipe.wait()
    cmd = 'git clone ' + repositoryURLOrPath + repositoryName  
    pipe = subprocess.Popen(cmd, shell=True, cwd=os.path.join(settings.MEDIA_ROOT, gitannex_dir))
    pipe.wait()
    cmd = 'git annex init ' + settings.PORTAL_NAME 
    pipe = subprocess.Popen(cmd, shell=True, cwd=os.path.join(settings.MEDIA_ROOT, gitannex_dir, repositoryName))
    pipe.wait()

def _selectRepositoryByPath():
    # Controlla il path del file ed estrai il nome del Repository
    return

def _getAvailableFolders(path):
    folderList = [( name , name ) for name in os.listdir(os.path.join(path, gitannex_dir)) \
                      if os.path.isdir(os.path.join(path, gitannex_dir, name))]
    return folderList

def gitAdd(fileName, repoDir):
    print 'git annex add ' + fileName
    cmd = 'git annex add ' + fileName
    pipe = subprocess.Popen(cmd, shell=True, cwd=repoDir)
    pipe.wait()

def gitCommit(fileTitle, authorName, authorEmail, repoDir):
    print 'git commit --author="' + authorName + ' <' + authorEmail +'>" -m "' + fileTitle + '"'
    cmd = 'git commit --author="' + authorName + ' <' + authorEmail +'>" -m "' + fileTitle + '"'
    pipe = subprocess.Popen(cmd, shell=True, cwd=repoDir)
    pipe.wait()

def gitPush(repoDir, remoteRepo):
    print 'git push ' + remoteRepo
    cmd = 'git push ' + remoteRepo
    pipe = subprocess.Popen(cmd, shell=True, cwd=repoDir)
    pipe.wait()

def gitAnnexMerge(repoDir):
    print 'git annex merge '
    cmd = 'git annex merge '
    pipe = subprocess.Popen(cmd, shell=True, cwd=repoDir)
    pipe.wait()

def gitPull(repoDir):
    print 'git pull '
    cmd = 'git pull '
    pipe = subprocess.Popen(cmd, shell=True, cwd=repoDir)
    pipe.wait()

def gitStatus(fileName, repoDir):
# Dovrebbe restituire oltre allo status un flag per avviare o no il sync
    cmd = 'git status'

@receiver_subclasses(post_save, MMedia, "mmedia_post_save")
def gitPostSave(instance, **kwargs):
    # In sender c'e' tutto.. user, filename, path
    # Salvo sul repository relativo alla cartella 
    # Bisogna organizzare i dati in cartelle ben strutturate
    # e mantenere una corrispondenza tra i GitAnnexRepository 
    # e la struttura di cartelle.
    print instance.mediatype
    print type(instance)
    print instance.path_relative()

    path = instance.path_relative().split(os.sep)
    if gitannex_dir in path:
        repositoryName = path[path.index(gitannex_dir) + 1]
        gitAnnexRep = GitAnnexRepository.objects.get(repositoryName__iexact=repositoryName)
        gitAdd(os.path.basename(instance.fileref.name), os.path.dirname(instance.fileref.path))
        gitCommit(instance.title, instance.author.username, instance.author.email, os.path.dirname(instance.fileref.path))


class GitAnnexRepository(models.Model):
    # Forse dovrei mettere qualcosa nella view. Esattamente.. Quando creo un repository questo puo' essere locale o remoto. 
    # Quindi devo poter scegliere tra una cartella locale (eventualmente crearla), o inserite un URL per effetuare il
    # clone (via ssh). 
    
    # Nella view va messo un if che a seconda chiama create o cloneRepository a seconda della scelta.

    # Codice di supporto da spostare nella view
#    filelisting = FileListing(MEDIA_ROOT, filter_func='filetype="Folder"', sorting_by=None, sorting_order=None)
#    availableFolders = filelisting.files_listing_filtered()
    repositoryName = models.CharField(max_length=60, choices=_getAvailableFolders(settings.MEDIA_ROOT))
    repositoryURLOrPath = models.CharField(max_length=200)
    syncStartTime = models.DateField()
    enableSync = models.BooleanField()
    remoteRepositoryURLOrPath = models.CharField(max_length=200)
    
    def createRepository(self):
        # Dovrebbe scegliere tra remoto e locale? 
        _createRepository(self.repositoryName, self.repositoryURLOrPath)
    
    def cloneRepository(self):
        _cloneRepository(self.repositoryURLOrPath, self.repositoryName)

    def syncRepository(self):
        if gitStatus:
            gitPull(self.repositoryURLOrPath, self.remoteReposittoryURLOrPath)
            gitAnnexMerge(self.repositoryURLOrPath)
            gitPush(self.repositoryURLOrPath, self.remoteReposittoryURLOrPath)
            
            # Signal to all that files should be synced 
            filesync_done.send(sender=self, repositoryName=self.repositoryName, repositoryDir=self.repositoryURLOrPath)
            
            # A questo punto bisogna ricreare gli oggetti in django a partire dal log di git.
            # Per ogni add si deve creare un oggetto prendendo il nome dall descrizione del commit
            # l'autore dall'autore del commit e il tipo dal path. 
            # Serializzazione? 

    def runScheduledJobs():
        allRep = GitAnnexRepository.objects.all()
        for rep in allRep:
            if rep.enableSync:
                if rep.syncStartTime >= datetime.datetime.now():
                    rep.syncRepository()

    def save(self, *args, **kwargs):
        self.createRepository()
        super(GitAnnexRepository, self).save(*args, **kwargs)


