# Copyright 2016 Alexey Grishchenko
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
import os
import logging
import pg8000
import time
import subprocess
import re

def raise_error(msg, out = None, err = None, isexit = True, code = 3):
    logging.error(msg)
    if out:
        logging.error("    STDOUT: %s" % out)
    if err:
        logging.error("    STDERR: %s" % err)
    if isexit:
        sys.exit(code)
    return

def execute_os(command):
    out = ''
    err = ''
    ret = 0
    try:
        pid = subprocess.Popen(command, shell=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
        (out, err) = pid.communicate()
        ret = pid.returncode
    except:
        raise_error('Exception ' + str(sys.exc_info()[1]))
    return (ret, out, err)

def execute_db(query, hasResult=True, canIgnore=False):
    res = None
    conn = pg8000.connect(user="vagrant", database="vagrant")
    cursor = conn.cursor()
    # Execute dummy command to bring up container
    try:
        cursor.execute(query)
    except:
        logging.error('Cannot execute this query:')
        logging.error(query)
        raise_error(str(sys.exc_info()[1]), isexit = (not canIgnore))
    conn.commit()
    if hasResult:
        res = cursor.fetchall()
    cursor.close()
    conn.close()
    return res

def getRepository():
    repo = execute_db("""
        select id, repo
            from repos
            where status is null
            order by id
            limit 1
        """)
    if repo is None or len(repo) == 0:
        logging.info("No more repositories to process")
        return None, None
    return repo[0][0], repo[0][1]

def cloneRepository(name, work_dir):
    attempts = 5
    sleep = 8
    reponame = name.split('/')[1].strip()
    logging.info("Cloning repository %s to %s/%s..." % (name, work_dir, reponame))
    while (attempts > 0):
        ret, out, err = execute_os ('rm -rf %s/%s' % (work_dir, reponame))
        if ret != 0:
            raise_error("Cannot remove directory %s/%s" % (work_dir, reponame),
                        out=out, err=err)
        ret, out, err = execute_os ('git clone https://github.com/%s.git %s/%s'
                                    % (name, work_dir, reponame))
        if ret != 0:
            raise_error("Cannot fetch repo %s" % name, out=out, err=err, isExit=False)
            time.sleep(sleep)
            sleep *= 2
            attempts -= 1
        else:
            break
    if attempts == 0:
        raise_error("Failed to fetch repo %s" % name)
    return

def finalizeRepository(name, work_dir):
    reponame = name.split('/')[1].strip()
    logging.info("Cleaning up repository %s in %s/%s..." % (name, work_dir, reponame))
    ret, out, err = execute_os ('rm -rf %s/%s' % (work_dir, reponame))
    if ret != 0:
        raise_error("Cannot remove directory %s/%s" % (work_dir, reponame),
                    out=out, err=err)
    execute_db("""
        update repos
            set status = 'ok'
            where repo = '%s'
        """ % name, hasResult = False)
    return

def insertCommit(id, commit, l1re, l2re):
    line1, line2 = commit.split('\n')
    l1 = l1re.match(line1)
    l2 = l2re.match(line2)
    if not l1 or not l2:
        raise_error("Cannot parse commit line with provided regexps: ", out=commit, isexit = False)
    else:
        insertions = '0'
        if l2.group(2):
            insertions = l2.group(2).strip(',').strip().split(' ')[0]
        deletions = '0'
        if l2.group(3):
            deletions = l2.group(3).strip(',').strip().split(' ')[0]
        query = """
            insert into commits
                (repo_id, commit_hash, author_name, author_email, commit_date,
                files_changed, insertions, deletions)
            values (%d, '%s', '%s', '%s', '%s'::timestamp,
                    %s, %s, %s)
            """ % (id, l1.group(1),
                       l1.group(2).replace("'", "''").replace("\\", "\\\\"),
                       l1.group(3).replace("'", "''").replace("\\", "\\\\"),
                       l1.group(4),
                   l2.group(1), insertions, deletions)
        execute_db(query, hasResult = False, canIgnore = True)
    return

def getCommits(name, id, work_dir):
    logging.info("Parsing commits for %s..." % name)
    reponame = name.split('/')[1].strip()
    repodir = '%s/%s' % (work_dir, reponame)
    ret, out, err = execute_os ("cd " + repodir +
            " && git log --pretty=format:'%H|%an|%ae|%ad' --shortstat --all")
    if ret != 0:
        raise_error("Cannot get commit logs", out=out, err=err)
    # Remove old commits if any
    execute_db("delete from commits where repo_id = %d" % id, hasResult = False)
    l1re = re.compile("([^|]*)\|([^|]*)\|([^|]*)\|\w+ (\w+ [0-9]+ [0-9\:]+ [0-9]+) .*")
    l2re = re.compile("\s+([0-9]+) \w+ changed(,\s+[0-9]+ insert\w+\(\+\))?(,\s+[0-9]+ del\w+\(\-\))?")
    for commit in out.split('\n\n'):
        commit = commit.strip()
        if len(commit.split('\n')) == 2:
            insertCommit(id, commit, l1re, l2re)
        else:
            commlen = len(commit.split('\n'))
            if commlen > 2:
                isout = 0
                lines = commit.split('\n')
                for i in range(len(lines)-1):
                    if l1re.match(lines[i]) and l2re.match(lines[-1]):
                        isout = 1
                        insertCommit(id, lines[i] + '\n' + lines[-1], l1re, l2re)
                if isout == 0:
                    logging.warning("Wrong formatted commit:")
                    print commit
    return

def process(work_dir):
    repoid, reponame = getRepository()
    while (reponame):
        cloneRepository(reponame, work_dir)
        getCommits(reponame, repoid, work_dir)
        finalizeRepository(reponame, work_dir)
        repoid, reponame = getRepository()
    return

def parse_input():
    if len(sys.argv) != 2:
        raise_error("Module requires a single input parameter - working dir")
    work_dir = sys.argv[1]
    if not os.path.isdir(work_dir):
        raise_error("Module requires a single input parameter - working dir")
    return work_dir

def main():
    reload(sys)
    sys.setdefaultencoding('utf8')
    logging.basicConfig(format='[%(levelname)s] %(asctime)s : %(message)s', level=logging.INFO)
    work_dir = parse_input()
    process(work_dir)

main()
