# coding:utf-8
# Generator for Yaonotes
import os
from pathlib import Path
import shutil
from jinja2 import Template, Environment, PackageLoader
import yaml
import datetime
from github import Github
from markdown2 import markdown


def generate_history():
    g = Github(os.getenv("GITHUB_TOKEN"))
    repo = g.get_repo("xzyaoi/yaonotes")
    contents = []
    commits = repo.get_commits()
    for each in commits:
        if each.get_statuses().totalCount > 0:
            content = {"name": each.sha,
                       "link": each.html_url,
                       "description": each.commit.message,
                       "lastUpdate": each.get_statuses()[0].updated_at or "Time Unknown"}
        else:
            content = {"name": each.sha,
                       "link": each.html_url,
                       "description": each.commit.message,
                       "lastUpdate": "Time Unknown"}
        contents.append(content)
    write_file(render(contents, "tpl/list.html"), "_site/history.html")


def create_folder(folder_path):
    try:
        os.makedirs(folder_path, exist_ok=True)
    except OSError:
        print("Creation of the directory %s failed" % folder_path)
    else:
        # print("Successfully created the directory %s " % folder_path)
        pass


def prepare():
    output_path = "./_site"
    try:
        shutil.rmtree(
            "./_site/assets",
        )
    except:
        pass
    create_folder(output_path)
    shutil.copytree(
        "assets/",
        "./_site/assets",
    )
    pathlist = Path("data").glob('./**')
    for each_path in pathlist:
        create_folder(each_path.__str__().replace("data/", "_site/"))


def render(content_list, tplfile):
    tpl = ""
    with open(tplfile, 'r') as f:
        tpl = f.read()
    template = Template(tpl)
    result = template.render(content=content_list, last_build=datetime.datetime.now(
    ).strftime("%b %d %Y %H:%M:%S"))
    return result


def read_data_file(filepath):
    result = []
    with open(filepath, 'r') as stream:
        try:
            result = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
    return result


def write_file(content, target):
    with open(target, 'w') as targetfile:
        targetfile.write(content)


def handle_yml(filepath, yml_file):
    folder_name = yml_file[:-4]
    create_folder(os.path.join("_site", filepath[5:], folder_name))
    target = os.path.join("_site", filepath[5:], folder_name, "index.html")
    contents = read_data_file(os.path.join(filepath, yml_file))
    if contents:
        write_file(render(contents, "tpl/list.html"), target)
    else:
        write_file(render([], "tpl/list.html"), target)


def get_all_contents(path):
    # print(path)
    contents = []
    subfolders = []
    if os.path.isdir(path):
        files = os.listdir(path)
        for each in files:
            if each.endswith(".yml"):
                handle_yml(path, each)
            abspath = os.path.join(path, each)
            if os.path.isdir(abspath):
                content = {"name": each.capitalize(), "link": each,
                           "description": each.capitalize()}
                subfolders.append(abspath)
                contents.append(content)
            elif abspath.endswith(".yml"):
                content = {
                    "name": each[:-4].capitalize(), "link": each[:-4], "description": each[:-4].capitalize()}
                subfolders.append(abspath)
                contents.append(content)
        write_file(render(contents, "tpl/list.html"),
                   os.path.join("_site", path[5:], "index.html"))

    return subfolders


def iterate_folders(base_path):
    if os.path.isdir(base_path):
        subfolders = get_all_contents(base_path)
        for each in subfolders:
            if os.path.isdir(each):
                iterate_folders(each)


def generate_blog_list(posts):
    write_file(render(posts, "tpl/list.html"),
               os.path.join("_site", "blogs", "index.html"))


def generate_blogs(path):
    posts = []
    blogs_contents = os.listdir(path)
    with open("tpl/content.html", 'r') as f:
        template_string = f.read()
    template = Template(template_string)
    for each in blogs_contents:
        with open(os.path.join(path, each)) as content_file:
            parsed_md = markdown(content_file.read(), extras=['metadata'])
            try:
                author = parsed_md.metadata['author']
            except Exception as e:
                author = "Xiaozhe Yao"
            posts.append({
                "author": author,
                "name": parsed_md.metadata['title'],
                "link": each.replace(".md",".html"),
                "description": parsed_md.metadata['summary'],
                "lastUpdate": parsed_md.metadata['datetime']
            })
            content_html = template.render(markdown_content=parsed_md,
                                           last_build=datetime.datetime.now().strftime("%b %d %Y %H:%M:%S"),
                                           markdown_title=parsed_md.metadata['title'],
                                           markdown_time=parsed_md.metadata['datetime'],
                                           summary=parsed_md.metadata['summary'])
            write_file(content_html, os.path.join("_site", "blogs",
                                                  each.replace(".md",".html")))

    generate_blog_list(posts)


def parse():
    # only for index.html
    index_content = "data/categories.yml"
    index_content = read_data_file(index_content)
    write_file(render(index_content, "tpl/list.html"), "_site/index.html")
    primary_folders = [
        os.path.join("data", subdir) for subdir in os.listdir("data")
    ]
    for each in primary_folders:
        if each == os.path.join("data", "blogs"):
            create_folder(os.path.join("_site", each[5:]))
            generate_blogs(each)
        else:
            create_folder(os.path.join("_site", each[5:]))
            iterate_folders(each)
    generate_history()


if __name__ == "__main__":
    prepare()
    parse()
