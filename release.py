import argparse
import subprocess
import sys

"""

This script is intended to allow a LIL Perma developer to reliably merge the
develop branch to stage, then the stage branch to master, and tag it. It is
derived from

https://github.com/harvard-lil/perma/blob/v0.169/perma_web/fabfile/deploy.py

Run something like this, from inside the repo, for which you must have
commit privileges:

    $ python3 ./release.py stage

or

    $ python3 ./release.py prod

"""


def main():
    if sys.version_info[0] < 3:
        raise Exception("Python 3 or a more recent version is required.")
    parser = argparse.ArgumentParser()
    parser.add_argument('tier', choices=['stage', 'prod'])
    parser.add_argument('--tag')
    args = parser.parse_args()
    if args.tier == 'stage':
        release_to_stage()
    elif args.tier == 'prod':
        tag_new_release(tag=args.tag)


def release_to_stage():
    """
        Roll develop into stage.
    """
    # re-create stage from develop and force push
    git("fetch upstream")
    git("branch -f stage upstream/develop")
    git("push upstream stage -f")


def tag_new_release(tag=None):
    """
        Roll stage into master and tag it.
    """
    git("fetch upstream")
    # figure out tag based on previous tags
    if not tag:
        last_release = max([int(tag.split('.')[1]) for tag in
                            git("tag", capture=True).decode().split("\n")
                            if tag.startswith("v0.")])
        this_release = input("Enter release number (default %d): "
                             % (last_release + 1))
        if not this_release:
            this_release = last_release + 1
        tag = "v0.%d" % this_release
    current_branch = git("rev-parse --abbrev-ref HEAD",
                         capture=True).strip().decode()
    try:
        # check out upstream/master
        git("checkout upstream/master")
        # merge upstream/stage and push changes to master
        git("merge upstream/stage -m 'Tagging %s. Merging stage into master'"
            % tag)
        git("push upstream HEAD:master")
        # tag release and push tag
        git("tag -a %s -m '%s'" % (tag, tag))
        git("push upstream --tags")
    finally:
        # switch back to the branch you were on
        git("checkout %s" % current_branch)


# helper
def git(cmd, capture=False):
    '''
    This is a wrapper around subprocess, something like a much-simplified
    version of Fabric 1's `local`, but renamed for concision and readability.
    See e.g.
    https://github.com/fabric/fabric/blob/aeb17ab1b1dc69b71b28557294c74158a137ee9d/fabric/operations.py#L1152-L1242
    '''
    cmdline = "git %s" % cmd
    if capture:
        return subprocess.check_output(cmdline, shell=True)
    else:
        return subprocess.call(cmdline, shell=True)


if __name__ == "__main__":
    main()
