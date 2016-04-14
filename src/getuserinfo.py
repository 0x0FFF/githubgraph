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
import logging
import pg8000
import json
from urllib2 import urlopen, Request

def raise_error(msg, out = None, err = None, isexit = True, code = 3):
    logging.error(msg)
    if out:
        logging.error("    STDOUT: %s" % out)
    if err:
        logging.error("    STDERR: %s" % err)
    if isexit:
        sys.exit(code)
    return

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

def parse(inStream):
    logging.info("Parsing user information...")
    res = {
        'id'        : '',
        'login'     : '',
        'url'       : '',
        'html_url'  : '',
        'repos_url' : '',
        'type'      : ''
    }
    jCommit = dict()
    data = inStream.read()
    try:
        jCommit = json.loads(data)
    except:
        logging.error('Cannot parse this json: %s' % data)
        raise_error("Stop to prevent issues")
    if 'author' in jCommit:
        jAuthor = jCommit['author']
        if jAuthor is not None and len(jAuthor) > 0:
            for token in res:
                if token in jAuthor:
                    res[token] = jAuthor[token]
    return res

def get_next_user():
    logging.info("Getting next user from database...")
    res = execute_db("""
        select  l.id,
                l.user_unique_id,
                l.repo,
                l.commit_hash
            from last_commit as l
                left join github_users as u
                on l.user_unique_id = u.user_unique_id
            where u.user_unique_id is null
                and l.status is null
            limit 1
        """)
    if res is None or len(res) == 0:
        return None, None, None, None
    return res[0]

def call_github_api(repo, commit_hash):
    logging.info("Fetching commit %s from %s..." % (commit_hash, repo))
    url = "https://api.github.com/repos/%s/commits/%s" % (repo, commit_hash)
    access_token = "PUT YOUR ACCESS TOKEN HERE"
    request = Request(url)
    request.add_header('Authorization', 'token %s' % access_token)
    response = urlopen(request)
    return response

def save_user(user_unique_id, user):
    if user['id'] != '':
        logging.info("Saving information of %s to database..." % user['login'])
        execute_db("delete from github_users where user_unique_id = %d" % user_unique_id, hasResult=False)
        execute_db("""
            insert into github_users (user_unique_id, id, login, url, html_url, repos_url, type)
                values (%d, %d, '%s', '%s', '%s', '%s', '%s')
            """ % (
                user_unique_id, int(user['id']),
                user['login'].replace("'", "''").replace("\\", "\\\\"),
                user['url'].replace("'", "''").replace("\\", "\\\\"),
                user['html_url'].replace("'", "''").replace("\\", "\\\\"),
                user['repos_url'].replace("'", "''").replace("\\", "\\\\"),
                user['type'].replace("'", "''").replace("\\", "\\\\")
            ), hasResult=False)
    else:
        logging.info("No user information found")
    return

def mark_processed(lc_id):
    execute_db("update last_commit set status='ok' where id = %d" % lc_id, hasResult=False)
    return

def process():
    lc_id, user_unique_id, repo, commit_hash = get_next_user()
    while (user_unique_id):
        stream = call_github_api(repo, commit_hash)
        user = parse(stream)
        save_user(user_unique_id, user)
        mark_processed(lc_id)
        lc_id, user_unique_id, repo, commit_hash = get_next_user()
    return

def main():
    reload(sys)
    sys.setdefaultencoding('utf8')
    logging.basicConfig(format='[%(levelname)s] %(asctime)s : %(message)s', level=logging.INFO)
    process()

main()
