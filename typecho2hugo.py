import argparse
import mysql.connector
import datetime
import os
import re
import shutil
import tarfile

POST_QUERY_SQL = '''
SELECT    u.screenname author,
          url          authorurl,
          title,
          type,
          text,
          created,
          c.status status,
          password,
          t2.category,
          t1.tags,
          slug
FROM      __TYPECHO_PREFIX__contents c
LEFT JOIN
          (
                   SELECT   cid,
                                     concat('"',group_concat(m.NAME separator '","'),'"') tags
                   FROM     __TYPECHO_PREFIX__metas m,
                            __TYPECHO_PREFIX__relationships r
                   WHERE    m.mid=r.mid
                   AND      m.type='tag'
                   GROUP BY cid ) t1
ON        c.cid=t1.cid
LEFT JOIN
          (
                   SELECT   cid,
                                     concat('"',group_concat(m.NAME separator '","'),'"') category
                   FROM     __TYPECHO_PREFIX__metas m,
                            __TYPECHO_PREFIX__relationships r
                   WHERE    m.mid=r.mid
                   AND      m.type='category'
                   GROUP BY cid) t2
ON        c.cid=t2.cid
LEFT JOIN
          (
                 SELECT uid,
                        screenname ,
                        url
                 FROM   __TYPECHO_PREFIX__users) AS u
ON        c.authorid = u.uid
WHERE     c.type IN ('post',
                     'page')
'''

POST_UPLOAD_PATTERN = r'(http.+)?/usr(/uploads/[^"\s)]+)'


parser = argparse.ArgumentParser(description='to hugo')

parser.add_argument('--host', type=str, default='localhost', help='host, default is localhost')
parser.add_argument('--port', type=int, default=3306, help='port, default is 3306')
parser.add_argument('--user', type=str, default='root', help='user, default is root')
parser.add_argument('--password', type=str, required=True, help='password')
parser.add_argument('--name', type=str, default='main', help='database name, default is main')
parser.add_argument('--prefix', type=str, default='typecho_', help='table prefix, default is typecho_')
parser.add_argument('--out', type=str, default='./typecho-exported', help='output directory, default is ./typecho-exported')
parser.add_argument('--typecho_root', type=str, default='', help='typecho install directory, use to convert path like <typecho>/usr/upload to relative path')

args = parser.parse_args()

if os.path.exists(args.out):
    shutil.rmtree(args.out)
os.makedirs(args.out, exist_ok=True)

content_save_dir = f'{args.out}/content'
os.makedirs(content_save_dir, exist_ok=True)

# connect to database
conn = mysql.connector.connect(
    host=args.host,
    port=args.port,
    user=args.user,
    password=args.password,
    database=args.name
)


cursor = conn.cursor(dictionary=True)

def export_posts(args, cursor):
    query = POST_QUERY_SQL.replace('__TYPECHO_PREFIX__', args.prefix)
    cursor.execute(query)
    results = cursor.fetchall()
    print(f'fetched {len(results)} rows')
    for row in results:
        title = row['title']
        slug = row['slug']
        created = row['created']
        tags = row['tags'] #if 'tags' in row and row['tags'] is not None else ''
        categories = row['category'] #if 'category' in row and row['category'] is not None else ''
        is_draft = "true" if row["status"] != "publish" or row["password"] else "false"
        post_type = row["type"]

        text = row['text'].replace('<!--markdown-->', '')
        
        # post created time
        dt = datetime.datetime.fromtimestamp(created)
        time_str = dt.strftime('%Y-%m-%dT%H:%M:%S.%f%z')
        year = dt.strftime('%Y')
        month = dt.strftime('%m')

        # dir to save this post
        # format 1 : posts/{year}/{month}/index.md
        post_dir = f'{content_save_dir}/post/{year}/{month}/{slug}'
        # format 2 : posts/{slug}
        #post_dir = f'{content_save_dir}/{slug}'
        post_filename = f'{post_dir}/index.md'
        
        # page-typed post, put it in root
        if not post_type == 'post':
            post_dir = f'{content_save_dir}'
            post_filename = f'{post_dir}/{slug}.md'
        
        os.makedirs(post_dir, exist_ok=True)
        
        print(f'[convert-post] draft={is_draft} {slug} {title} {time_str} {year} {month}')
        
        # replace /usr/upload to relative path
        if not args.typecho_root == '':
            new_text = ""
            image_dir = os.path.join(post_dir, 'images')
            os.makedirs(image_dir, exist_ok=True)
            matches = re.finditer(POST_UPLOAD_PATTERN, text, re.MULTILINE)
            last_end = 0
            for match in matches:
                start, end = match.span()
                source_image = match.group(2)
                name = os.path.basename(source_image)
                target_image_file = f'{image_dir}/{name}'
                source_image_file = f'{args.typecho_root}/usr/{source_image}'
                print(f'[transfer-image-path] {source_image_file} to {target_image_file}')
                shutil.copyfile(source_image_file, target_image_file)
                new_text += text[last_end:start] + "images/" + name
                last_end = end
            new_text += text[last_end:]
            text = new_text
        
        # write to file
        with open(post_filename, "w", encoding='utf-8') as w:
            w.write(f'---\n'
                    f'title: "{title}"\n'
                    f'categories: [ {categories} ]\n'
                    f'tags: [ {tags} ]\n'
                    f'draft: {is_draft}\n'
                    f'slug: "{slug}"\n'
                    f'date: "{time_str}"\n'
                    f'---\n\n')
            w.write(text)
            w.write('\n')
            w.flush()

    print(f'[done] converted posts under {content_save_dir}')

def export_comments(args, cursor):
    # todo
    pass
export_posts(args, cursor)

export_comments(args, cursor)


output_tar = f'{args.out}.tar.gz'
print(f'[output] compressing to {output_tar} ...')

with tarfile.open(output_tar, "w:gz") as tar:
    tar.add(args.out, arcname=os.path.basename(args.out))

cursor.close()
conn.close()


