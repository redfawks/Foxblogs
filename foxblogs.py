#!/usr/bin/python

import time
import datetime
import configparser
import codecs
import markdown
import glob
import os
import re
import textwrap
from bs4 import BeautifulSoup

class configuration(object):
    def __init__(self, cfgfile):
        __config = configparser.RawConfigParser()
        __config.read(cfgfile)
    
        self.meta = {
            'lang' : __config.get('meta', 'language')
        }

        self.content = {
            'title' : __config.get('content', 'title'),
            'heading' : __config.get('content', 'heading'),
            'subheading' : __config.get('content', 'subheading'),
            'footer' : __config.get('content', 'footer')
        }

        self.impressum = {
            'available' : __config.getboolean('impressum', 'available'),
            'name' : __config.get('impressum', 'name'),
            'addr' : __config.get('impressum', 'address'),
            'zip' : __config.get('impressum', 'zip'),
            'city' : __config.get('impressum', 'city')
        }
        
        self.settings = {
            'date_fmt' : __config.get('settings', 'date_fmt'),
            'css' : __config.get('settings', 'css'),
            'dir_root' : __config.get('settings', 'root_dir'),
            'dir_md' : __config.get('settings', 'md_dir'),
            'dir_html' : __config.get('settings', 'html_dir'),
            'about' : __config.get('settings', 'about'),
            'preview_words' : __config.getint('settings', 'preview_words'),
            'prevs_per_page' : __config.getint('settings', 'previews_per_page')
        }

class article(object):
    def __init__(self, settings, mdfile):
        self.settings = settings
        input_file = codecs.open(mdfile, mode='r', encoding='utf-8')
        self.fullmd = input_file.read()
        self.previewlength = settings.settings['preview_words']
        self.md = markdown.Markdown(extensions = ['markdown.extensions.meta'])
        self.fullhtml = self.md.convert(self.fullmd)
        
    def get_metadata(self):
        return(self.md.Meta)
    
    def get_txt_html(self):
        return(self.fullhtml)
    
    def get_txt_md(self):
        return(self.fullmd)
    
    def get_txt_plain(self):
        return(''.join(BeautifulSoup(self.fullhtml, 'lxml').findAll(text=True)))
    
    def get_txt_plain_preview(self):
        fullplain = self.get_txt_plain()
        singlewords = fullplain.split()
        previewtext = ' '.join(singlewords[0:self.previewlength])
        return(previewtext)
    
    def get_link_filename(self):
        title = self.get_metadata()['title'][0]
        date = self.get_metadata()['date'][0]
        regex = '[^0-9a-zA-Z _-äöüÄÖÜ]'
        title_fixed = re.sub(regex, '', title)
        title_fixed = title_fixed.lower()
        title_fixed = title_fixed.replace(u'ä', 'ae')
        title_fixed = title_fixed.replace(u'ö', 'oe')
        title_fixed = title_fixed.replace(u'ü', 'ue')
        title_fixed = title_fixed.replace('_', '-')
        title_fixed = title_fixed.replace(' ', '-')
        tstmp = str(time.mktime(datetime.datetime.strptime(date, self.settings.settings['date_fmt']).timetuple()))
        full_link = tstmp.split('.')[0] + '_' + title_fixed + '.html'
        return(full_link)
        
        
class fullpage(object):
    def __init__(self, settings):
        self.settings = settings
        self.__html_head = """\
            <!DOCTYPE html>
            <html lang="{0}">
                <head>
                    <meta charset="utf-8" />
                    <link rel="stylesheet" href="{1}" />
                    <title>{2}</title>
                </head>\
        """.format(self.settings.meta['lang'], self.settings.settings['css'], settings.content['title'])
        
        self.__html_banner = """
                <body>
                    <div id=header>
                        <h1>{0}</h1>
                        <h3>{1}</h3>
                    </div>
        """.format(self.settings.content['heading'], self.settings.content['subheading'])
        
        self.__html_menu = """
                    <div id="menu">
                        <div class="menu_item-l"><a href='menu_0.html'>Home</a></div>
                        <div class="menu_item-m"><a href='proj_0.html'>Projects</a></div>
                        <div class="menu_item-r"><a href='about.html'>About</a></div>
                    </div>
                    <div id="contentbody">\
        """
        
        self.__html_article = """
                        <div class="article">
                            {0}
                            <h2>{1}</h2>
                            <p>{2}</p>
                        </div>\
                        <div id="author">{3}</div>\
        """
                
        self.__html_preview = """
                        <div class="article_preview">
                            {0}
                            <h2>{1}</h2>
                            <p>{2}</p>
                            <a href="{3}">Full article</a>
                        </div>\
        """
        
        self.__html_navigation = """
                        <div id="navigation">
                            <div id="navigation-fwd">
                                {0}
                            </div>
                            <div id="navigation-back">
                                {1}
                            </div>
                        </div>\
        """
        
        self.__html_footer = """
                    </div>
                    <div id="footer">
                        {0}
                    </div>
                </body>
            </html>\
        """.format(self.settings.content['footer'])
    
    def __generate_body_summary(self, articles):
        bodycontent = ""
        for article in articles:
            meta = article.get_metadata()
            bodycontent += self.__html_preview.format(meta['date'][0], meta['title'][0], article.get_txt_plain_preview(), article.get_link_filename())
        return(bodycontent)

    def __generate_body_article(self, article):
        meta = article.get_metadata()
        bodycontent = self.__html_article.format(meta['date'][0], meta['title'][0], article.get_txt_html(), meta['author'][0])
        return(bodycontent)
    
    def generate_full_summary(self, articles, page_id, link_fwd, link_back):
        fullhtml = self.__html_head
        fullhtml += self.__html_banner
        fullhtml += self.__html_menu
        fullhtml += self.__generate_body_summary(articles)
        if link_fwd == True:
            link_fwd_html = "<a href=menu_{0}.html>&lt;- Newer Entries</a>".format(page_id-1)
        else:
            link_fwd_html = "&lt;- Newer Entries"
        
        if link_back == True:
            link_back_html = "<a href=menu_{0}.html>Older Entries -&gt;</a>".format(page_id+1)
        else:
            link_back_html = "Older Entries -&gt;"
        fullhtml += self.__html_navigation.format(link_fwd_html, link_back_html)
        fullhtml += self.__html_footer.format(self.settings.content['footer'])
        return(textwrap.dedent(fullhtml))
    
    def generate_full_article(self, article):
        fullhtml = self.__html_head
        fullhtml += self.__html_banner
        fullhtml += self.__html_menu
        fullhtml += self.__generate_body_article(article)
        fullhtml += self.__html_footer
        return(textwrap.dedent(fullhtml))


class article_handler(object):
    def __init__(self, settings):
        self.settings = settings
        md_files = os.listdir(settings.settings['dir_root'] + '/' + settings.settings['dir_md'])
        articles_parsed = self.__read_articles(md_files)
        self.articles_sorted = self.__sort_articles(articles_parsed)
    
    def __read_articles(self, filelist):
        articles = list()
        for mdfile in filelist:
            articles.append(article(self.settings, self.settings.settings['dir_root'] + '/' + self.settings.settings['dir_md'] + '/' + mdfile))
        return(articles)
    
    def __sort_articles(self, articles):
        articles_sorted = sorted(articles, key=lambda article: datetime.datetime.strptime(article.get_metadata()['date'][0], self.settings.settings['date_fmt']), reverse=True)
        return(articles_sorted)

    def get_article_list(self):
        return(self.articles_sorted)

    def get_html_about(self):
        about_article = article(self.settings, self.settings.settings['dir_root'] + '/' + self.settings.settings['about'])
        about_page = fullpage(self.settings)
        return(about_page.generate_full_article(about_article))

    def get_html_overview_pages(self):
        html_pages = list()
        single_page_articles = list()
        cnt_per_page = 0
        cnt_articles = 0
        cnt_pages = 0
        for article in self.articles_sorted:
            if cnt_per_page < self.settings.settings['prevs_per_page']-1 and cnt_articles != len(self.articles_sorted)-1:
                single_page_articles.append(article)
                cnt_per_page = cnt_per_page + 1
            else:
                single_page_articles.append(article)
                single_page = fullpage(self.settings)
                if cnt_pages == 0:
                    link_fwd = False
                else:
                    link_fwd = True
                
                if cnt_articles == len(self.articles_sorted)-1:
                    link_back = False
                else:
                    link_back = True
                
                html_pages.append(single_page.generate_full_summary(single_page_articles, cnt_pages, link_fwd, link_back))
                cnt_pages = cnt_pages + 1
                single_page_articles = []
                cnt_per_page = 0
            cnt_articles = cnt_articles + 1
            
        html_pages_named = list()
        cnt = 0
        for page in html_pages:
            html_pages_named.append(('menu_' + str(cnt) + '.html', page))
            cnt = cnt + 1
        return(html_pages_named)
    
    def get_html_article_pages(self):
        html_pages_named = list()
        for article in self.articles_sorted:
            single_page = fullpage(self.settings)
            html_pages_named.append((article.get_link_filename(), single_page.generate_full_article(article)))
        return(html_pages_named)
    
    def write_html_files(self):
        fullpath = self.settings.settings['dir_root'] + '/' + self.settings.settings['dir_html'] + '/' + 'about.html'
        outfile = open(fullpath, 'w')
        outfile.write(self.get_html_about())
        outfile.close()
        for overview_html_file in self.get_html_overview_pages():
            fullpath = self.settings.settings['dir_root'] + '/' + self.settings.settings['dir_html'] + '/' + overview_html_file[0]
            outfile = open(fullpath, 'w')
            outfile.write(overview_html_file[1])
            outfile.close()
        for article_html_file in self.get_html_article_pages():
            fullpath = self.settings.settings['dir_root'] + '/' + self.settings.settings['dir_html'] + '/' + article_html_file[0]
            outfile = open(fullpath, 'w')
            outfile.write(article_html_file[1])
            outfile.close()

settings = configuration('config.ini')
articles = article_handler(settings)
articles.write_html_files()
