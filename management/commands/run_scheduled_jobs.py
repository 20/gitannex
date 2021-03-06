# you MUST import the management classes like this:
from django.core.management.base import NoArgsCommand, CommandError

# import any models or stuff you need from your project
from gitannex.models import GitAnnexRepository, runScheduledJobs

# your custom command must reference the base management classes like this:
class Command(NoArgsCommand):
    # it's useful to describe what the function does:
    help = 'Run scheduled jobs related to git repositories'

    def handle_noargs(self, **options):
        runScheduledJobs()
        
