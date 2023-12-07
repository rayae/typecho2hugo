# typecho2hugo

A pythons script that export typecho posts to hugo

## Requirements

```shell
pip3 install mysql-connector-python==8.0.6
# or
pip3 install -r requirements.txt
```

## Usage

```shell
usage: export-typecho2hugo.py [-h] [--host HOST] [--port PORT] [--user USER] --password PASSWORD [--name NAME]
                              [--prefix PREFIX] [--out OUT] [--typecho_root TYPECHO_ROOT]

to hugo

optional arguments:
  -h, --help            show this help message and exit
  --host HOST           host, default is localhost
  --port PORT           port, default is 3306
  --user USER           user, default is root
  --password PASSWORD   password
  --name NAME           database name, default is main
  --prefix PREFIX       table prefix, default is typecho_
  --out OUT             output directory, default is ./typecho-exported
  --typecho_root TYPECHO_ROOT
                        typecho install directory, use to convert path like <typecho>/usr/upload to relative path
```

## Example

```shell
python3 ./typecho2hugo.py --host 127.0.0.1 --user root --password 123456 --name typecho --prefix typecho_ --out hugo
```
