#coding:utf-8
#source :https://iplists.firehol.org
#source ID:1
#IP type
#date:2017-10-9

import urllib2
import re
import threading
import time
import datetime
import Queue
import json
import MySQLdb
import sys
import socket
import os

thnum = 0
page = '' #存放被打开的网页
DownList = Queue.Queue()
queueLocker = threading.Lock()

#取回页面并保存成文件
def GetThePage(url,name,time,fm):
	headers = {'User-Agent' : 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'}
	request = urllib2.Request(url, None, headers)
	try:
		response = urllib2.urlopen(request,timeout=10)
	except urllib2.HTTPError as e:
		try:
			URL = 'https://iplists.firehol.org/files/%s.ipset'%name
			request2 = urllib2.Request(URL,None,headers)
			response2 = urllib2.urlopen(request2,timeout=10)
		except urllib2.HTTPError as e:
			print url
			pass
		except:
			global thnum
			thnum -= 1
			pass
		else:
			PAGE = response2.read()
			File = open("%s%s.%s"%(name,time,fm),'wb+')
			File.write((PAGE))
	except urllib2.URLError as e:
		print e.reason
		pass
	else:
		global page
		page = response.read()
		filename = "%s_%s.%s"%(name,time,fm)
		FILE = open(filename,'wb+')
		FILE.write(page)


#处理页面提取其中的URL
def DisposePage(PageName):
	with open(PageName,'r') as f:
		DownData = json.load(f)
		lenth = len(DownData)
	for count in xrange(0,lenth):
		name = DownData[count]['ipset']
		downurl = "https://iplists.firehol.org/files/%s.netset"%name
		time = str(datetime.datetime.utcfromtimestamp(DownData[count]['updated']/1000))
		doc = {'name':name,'downurl':downurl,'time':time}
		print doc
		DownList.put(doc)

#多线程下载最终的文件
class DownFile(threading.Thread):
	"""docstring for DownFile"""
	def __init__(self):
		threading.Thread.__init__(self)
		self.queue = DownList
	def run(self):
		global thnum
		while True:
			if not self.queue.empty():
				queueLocker.acquire()
				DownDoc = DownList.get()
				queueLocker.release()
				GetThePage(DownDoc['downurl'],DownDoc['name'],DownDoc['time'],'html')
			else:
				thnum -=1
				print thnum
				break

def get_ip(string_ip):
	result = re.findall(r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b", string_ip)
	if result:
		return result
	else:
		return 'None'


if __name__ == '__main__':
	#get all the file in the list except 46.py
	PATH_before = os.getcwd()
	s_before = os.listdir(PATH_before.encode('utf-8'))
	s_before.remove('1.py')
	for each in s_before:
		os.remove(each)

	GetThePage('http://iplists.firehol.org/all-ipsets.json','data','20170925','json')
	global page
	DisposePage('data_20170925.json')
	global thnum

	for i in xrange(0,10):
		t = DownFile()
		thnum += 1
		try:
			t.start()
			print "start"
		except:
			pass
	while True:
		time.sleep(6)
		if thnum == 1:
			break

#将下载好的文件按时间、IP、来源存入数据库
	source_id = '1'
	print 'DATABASE'
	PATH = os.getcwd()
	s = os.listdir(PATH.encode('utf-8'))
	s.remove('1.py')
	s.remove('data_20170925.json')#then we get all the revoled files' name
	FILE = open('FILE.txt','w')
	for eachfile in s:
		FILE.write(eachfile+'\n')#? '\n'
	FILE.close()
	#start database according to the FILE.TXT
	file_list = open('FILE.txt','r')
	for eachfile in file_list:
		# #insert data into 'ip_table' table
		db = MySQLdb.connect(user='',db='',passwd='',host='',charset='utf8')#在相应位置填上你的数据库信息
		cursor = db.cursor()
		eachfile= eachfile.strip('\n')
		print 'file :',file
		web_file = open(eachfile,'r')
		for eachline in web_file:
			if '#' in eachline:
				if 'Category' in eachline:
					stamp_parameter = eachline.split(':')
					stamp = stamp_parameter[1].strip()
					print 'stamp :',stamp
				if 'This File Date' in eachline:
					eachline_parameters = eachline.split(':',1)
					time_part = eachline_parameters[1]
					time_part_parameters = time_part.split('UTC')
					date_time = time_part_parameters[0] +time_part_parameters[1].strip()
					update_time = date_time[1:]
					print 'time :',update_time
			else:
				ip =  eachline.strip('\n').strip()
				ip_group = get_ip(ip)
				if ip_group == 'None':
					continue
				else:
					for ip in ip_group:
						print 'ip :',ip
						cursor.execute("REPLACE INTO ip_table(ip,update_time,source,stamp) VALUES('%s','%s','%s','%s')" % (ip,update_time,source_id,stamp))
		db.commit()
		db.close()

exit()
