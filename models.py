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
import logging

logger = logging.getLogger(__name__)
gitannex_dir = settings.GITANNEX_DIR

def _createRepository(repositoryName, remoteRepositoryURLOrPath):
    logger.info('git config --global user.name "admin"')
    cmd = 'git config --global user.name "admin"' 
    pipe = subprocess.Popen(cmd, shell=True, cwd=os.path.join(settings.MEDIA_ROOT, gitannex_dir, repositoryName))
    pipe.wait()
    logger.info('git config --global user.email "admin@mocambos.net"')
    cmd = 'git config --global user.email "admin@mocambos.net"' 
    pipe = subprocess.Popen(cmd, shell=True, cwd=os.path.join(settings.MEDIA_ROOT, gitannex_dir, repositoryName))
    pipe.wait()
    logger.info('git init')
    cmd = 'git init' 
    pipe = subprocess.Popen(cmd, shell=True, cwd=os.path.join(settings.MEDIA_ROOT, gitannex_dir, repositoryName))
    pipe.wait()
    logger.info('git annex init ' + settings.PORTAL_NAME)
    cmd = 'git annex init ' + settings.PORTAL_NAME 
    pipe = subprocess.Popen(cmd, shell=True, cwd=os.path.join(settings.MEDIA_ROOT, gitannex_dir, repositoryName))
    pipe.wait()
    # TODO: Manage repositories dinamically 
    logger.info('git remote add baoba ' + remoteRepositoryURLOrPath)
    cmd = 'git remote add baoba ' + remoteRepositoryURLOrPath 
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

def gitCommit(fileTitle, authorName, authorEmail, repoDir):
    logger.info('git commit --author="' + authorName + ' <' + authorEmail +'>" -m "' + fileTitle + '"')
    cmd = 'git commit --author="' + authorName + ' <' + authorEmail +'>" -m "' + fileTitle + '"'
    pipe = subprocess.Popen(cmd, shell=True, cwd=repoDir)
    pipe.wait()

def gitPush(repoDir):
    logger.info('git push ')
    cmd = 'git push '
    pipe = subprocess.Popen(cmd, shell=True, cwd=repoDir)
    pipe.wait()

def gitPull(repoDir):
    logger.info('git pull ')
    cmd = 'git pull '
    pipe = subprocess.Popen(cmd, shell=True, cwd=repoDir)
    pipe.wait()

def gitStatus(fileName, repoDir):
# Dovrebbe restituire oltre allo status un flag per avviare o no il sync
    cmd = 'git status'

def gitGetSHA(repoDir):
    logger.info('git rev-parse HEAD')
    cmd = 'git rev-parse HEAD'
    pipe = subprocess.Popen(cmd, shell=True, cwd=repoDir)
    output,error = pipe.communicate()
    logger.debug('>>> Revision is: ' + output)
    return output

def gitAnnexAdd(fileName, repoDir):
    logger.info('git annex add ' + fileName)
    cmd = 'git annex add ' + fileName
    pipe = subprocess.Popen(cmd, shell=True, cwd=repoDir)
    pipe.wait()

def gitAnnexMerge(repoDir):
    logger.info('git annex merge ')
    cmd = 'git annex merge '
    pipe = subprocess.Popen(cmd, shell=True, cwd=repoDir)
    pipe.wait()

def gitAnnexCopyTo(repoDir):
    # TODO: Next release with dynamic "origin" 
    logger.info('git annex copy --fast --to origin ')
    cmd = 'git annex copy --fast --to origin'
    pipe = subprocess.Popen(cmd, shell=True, cwd=repoDir)
    pipe.wait()

def gitAnnexGet(repoDir):
    # TODO: Next release with possibility to choice what to get 
    logger.info('git annex get .')
    cmd = 'git annex get .'
    pipe = subprocess.Popen(cmd, shell=True, cwd=repoDir)
    pipe.wait()

# Connecting to MMedia signal
@receiver_subclasses(post_save, MMedia, "mmedia_post_save")
def gitMMediaPostSave(instance, **kwargs):
    logger.debug(instance.mediatype)
    logger.debug(type(instance))
    logger.debug(instance.path_relative())

    path = instance.path_relative().split(os.sep)
    if gitannex_dir in path:
        repositoryName = path[path.index(gitannex_dir) + 1]
        gitAnnexRep = GitAnnexRepository.objects.get(repositoryName__iexact=repositoryName)
        gitAnnexAdd(os.path.basename(instance.fileref.name), os.path.dirname(instance.fileref.path))
        gitCommit(instance.title, instance.author.username, instance.author.email, os.path.dirname(instance.fileref.path))

def runScheduledJobs():
    allRep = GitAnnexRepository.objects.all()
    for rep in allRep:
        if rep.enableSync:
            # TODO: Manage time of syncing
            # if rep.syncStartTime >= datetime.datetime.now():
            rep.syncRepository()


class GitAnnexRepository(models.Model):
    # Forse dovrei mettere qualcosa nella view. Esattamente.. Quando creo un repository questo puo' essere locale o remoto. 
    # Quindi devo poter scegliere tra una cartella locale (eventualmente crearla), o inserite un URL per effetuare il
    # clone (via ssh). 
    # Nella view va messo un if che a seconda chiama create o cloneRepository a seconda della scelta.

    repositoryName = models.CharField(max_length=60, choices=_getAvailableFolders(settings.MEDIA_ROOT))
    repositoryURLOrPath = models.CharField(max_length=200)
    syncStartTime = models.DateField()
    enableSync = models.BooleanField()
    remoteRepositoryURLOrPath = models.CharField(max_length=200)
#    lastSyncSHA = models.CharField(max_length=100)

    def createRepository(self):
        # Dovrebbe scegliere tra remoto e locale? 
        _createRepository(self.repositoryName, self.remoteRepositoryURLOrPath)
    
    def cloneRepository(self):
        _cloneRepository(self.repositoryURLOrPath, self.repositoryName)

    def syncRepository(self):
        gitPull(self.repositoryURLOrPath)
        gitAnnexMerge(self.repositoryURLOrPath)
        gitPush(self.repositoryURLOrPath)
        gitAnnexCopyTo(self.repositoryURLOrPath)
        # TODO: Next release with possibility to choice what to get 
        gitAnnexGet(self.repositoryURLOrPath)
        # TODO: Next release with selective sync since a given revision (using git SHA)
        # self.lastSyncSHA = gitGetSHA(self.repositoryURLOrPath)
        # Signal to all that files are (should be) synced 
        logger.debug(">>> BEFORE filesync_done")
        filesync_done.send(sender=self, repositoryName=self.repositoryName, \
                               repositoryDir=self.repositoryURLOrPath)
        logger.debug(">>> AFTER filesync_done")

    def save(self, *args, **kwargs):
        self.createRepository()
        super(GitAnnexRepository, self).save(*args, **kwargs)


