# coding: utf-8
from flask import Flask,render_template,url_for
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import Length, Required, URL
from bs4 import BeautifulSoup
import urllib.request
from urllib.parse import urljoin
import os
import pickle

app = Flask(__name__)
app.secret_key = 'AskfjghjdsaDFkrdnaladfae'

#データベース
import sqlite3
class Database():
    def __init__(self):
        dbpath=os.path.join(app.root_path, 'database.db')
        connection=sqlite3.connect(dbpath)
        cursor = connection.cursor()
        connection.isolation_level = None
        self.connection = connection
        self.cursor = cursor
    def close(self):
        connection = self.connection
        connection.commit()
        connection.close()

    def reset(self):
        cursor = self.cursor
        try: #テーブルを作成
            cursor.execute("DROP TABLE IF EXISTS url_list")
            cursor.execute("CREATE TABLE IF NOT EXISTS url_list (url TEXT, img_src TEXT, title TEXT, description TEXT, count INTEGER)")
        except sqlite3.Error as e:
            print('sqlite3.Error occurred:', e.args[0])

    def insert(self,url_info):
        cursor=self.cursor
        cursor.execute("INSERT INTO url_list VALUES (?,?,?,?,1)" , (url_info[0],url_info[1],url_info[2],url_info[3]))

    def update(self,url_info):
        cursor=self.cursor
        cursor.execute("UPDATE url_list set url=?,img_src=?,title=?,description=?,count=count+1 where url='%s'" % url_info[0],('%s' % url_info[0],'%s' % url_info[1],'%s' % url_info[2],'%s' % url_info[3]))

    def order_asc(self,sort,num):
        cursor=self.cursor
        cursor.execute('SELECT * FROM url_list ORDER BY %s ASC LIMIT %s' % (sort,num) ) # ここはステークホルダー
        data_list = cursor.fetchall()
        return data_list

    def order_desc(self,sort,num):
        cursor=self.cursor
        cursor.execute('SELECT * FROM "url_list" ORDER BY %s DESC LIMIT %s' % (sort,num))# ここはステークホルダー
        data_list = cursor.fetchall()
        return data_list

    def search(self,search_url):
        cursor=self.cursor
        url_data = cursor.execute('SELECT url FROM url_list WHERE url="%s"' % search_url)
        url_data = cursor.fetchall()
        return url_data

    def confirm(self,url_info):
        cursor=self.cursor
        url_data = self.search(url_info[0])
        if len(url_data) > 0:
            print("存在します")
            self.update(url_info)
        else:
            print("存在しません")
            self.insert(url_info)

class UrlForm(FlaskForm):
    url = StringField(
        label='URL：',
        validators=[
            Required('URLを入力してください'),
            Length(min=1, max=1024, message='URLは1024文字以内で入力してください'),
            URL(message='URLが正しくありません'),
        ])

@app.route('/', methods=['GET', 'POST'])
def send_url():
    form = UrlForm()
    if form.validate_on_submit():
        url = form.url.data
        # print('送られたURLは {} だよ'.format(url))

        req = urllib.request.Request(url)
        response = urllib.request.urlopen(req)
        html = response.read()
        soup = BeautifulSoup(html, "lxml")

        link_card = "width:100%;max-width:700px;height:100px;border:2px solid #000;border-radius:4px;overflow:hidden;padding:5px !important;background:#fff !important;"
        fit_link = "display:block;width:100%;height:100%;text-decoration:none;color:#000;"
        try:
            img_src = soup.find("meta",{"property":"og:image"}).get("content")
        except:
            try:
                img_url = soup.body.find("img").get("src")
                img_src = urljoin(url, img_url)
            except:
                img_src = url_for('static', filename='images/noimage.png')

        img_style = "float:left;width:80px;height:80px;margin:5px 10px 5px 5px !important;"
        title_style = "font-size:80%;font-weight:bold;margin:5px;"
        title = soup.title.text
        hr_style = "margin:5px 5px 10px 90px !important;"
        description_style = "font-size:55%;"
        try:
            description = soup.find("meta",{"name":"description"}).get("content")
        except:
            try:
                description = soup.p.text[0:100]+"..."
            except:
                try:
                    description = soup.body.text[0:100]+"..."
                except:
                    description = ""
        link_code = "<div style=\"%s\"><a href=\"%s\" style=\"%s\"><img src=\"%s\" alt=\"\" style=\"%s\"><span style=\"%s\">%s</span><hr style=\"%s\"><span style=\"%s\">%s</span></a></div>" % (link_card,url,fit_link,img_src,img_style,title_style,title,hr_style,description_style,description)

        #データの読み書き
        Data=Database()
        #Data.reset()
        url_info = (url,img_src,title,description)
        Data.confirm(url_info)
        data_list = Data.order_desc("count",10)
        print(data_list)
        #データベースを保存して閉じる
        Data.close()

        return render_template('index.html', form=form,link_card=link_card,url=url,fit_link=fit_link,img_src=img_src,img_style=img_style,title_style=title_style,title=title,hr_style=hr_style,description=description,description_style=description_style, link_code=link_code,data_list=data_list)

    else:
        Data=Database()
        data_list = Data.order_desc("count",10)
        Data.close()
        return render_template('index.html', form=form,data_list=data_list)

# アプリケーションの実行
if __name__ == '__main__':
    app.run()
    #app.run(debug=True)
