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

def parse_json(jActivity):
    res = []
    if isinstance(jActivity, list):
        for obj in jActivity:
            res.extend(parse_json(obj))
    elif isinstance(jActivity, dict):
        for tag in jActivity:
            if tag == "repo" and jActivity[tag] is not None:
                res.append(
                    {
                        'id': jActivity[tag].get('id'),
                        'full_name': jActivity[tag].get('full_name'),
                        'name': jActivity[tag].get('name'),
                        'url': jActivity[tag].get('url')
                    } )
            else:
                res.extend(parse_json(jActivity[tag]))
    return res

def parse(inStream):
    logging.info("Parsing activity information...")
    jActivity = dict()
    data = inStream.read()
    try:
        jActivity = json.loads(data)
    except:
        logging.error('Cannot parse this json: %s' % data)
        raise_error("Stop to prevent issues")
    res = parse_json(jActivity)
    return res

def get_next_user():
    logging.info("Getting next user from database...")
    res = execute_db("""
        select  user_unique_id,
                id,
                login
            from github_users
            where processed = 0
            limit 1
        """)
    if res is None or len(res) == 0:
        return None, None, None
    return res[0]

def call_github_api(username):
    logging.info("Fetching public activity of %s..." % username)
    url = "https://api.github.com/users/%s/events/public" % (username)
    access_token = "PUT YOUR GIT ACCESS TOKEN HERE"
    request = Request(url)
    request.add_header('Authorization', 'token %s' % access_token)
    response = urlopen(request)
    return response

# TODO: change
def save_user(user_unique_id, username, info):
    logging.info("Saving information of %s to database..." % username)
    execute_db("delete from github_activity where user_unique_id = %d" % user_unique_id, hasResult=False)
    for obj in info:
        rid, name, url = '', '', ''
        if "id" in obj and obj["id"] is not None:
            rid = obj["id"]
        if "full_name" in obj and obj["full_name"] is not None:
            name = obj["full_name"]
        elif "name" in obj and obj["name"] is not None:
            name = obj["name"]
        if "url" in obj and obj["url"] is not None:
            url = obj["url"]
        execute_db("""
            insert into github_activity (user_unique_id, login, repo_id, repo_name, repo_url)
                values (%d, '%s', %d, '%s', '%s')
            """ % (
                int(user_unique_id),
                username.replace("'", "''").replace("\\", "\\\\"),
                int(rid) if rid != '' else -1,
                name.replace("'", "''").replace("\\", "\\\\"),
                url.replace("'", "''").replace("\\", "\\\\"),
            ), hasResult=False)
    return

def mark_processed(user_unique_id):
    execute_db("update github_users set processed = 1 where user_unique_id = %d" % user_unique_id, hasResult=False)
    return
    
def mark_bad(user_unique_id):
    execute_db("update github_users set processed = -1 where user_unique_id = %d" % user_unique_id, hasResult=False)
    return

def process():
    user_unique_id, id, username = get_next_user()
    while (user_unique_id):
        try:
            stream = call_github_api(username)
            info = parse(stream)
            save_user(user_unique_id, username, info)
            mark_processed(user_unique_id)
        except:
            mark_bad(user_unique_id)
        user_unique_id, id, username = get_next_user()
    return

def main():
    reload(sys)
    sys.setdefaultencoding('utf8')
    logging.basicConfig(format='[%(levelname)s] %(asctime)s : %(message)s', level=logging.INFO)
    process()

main()
