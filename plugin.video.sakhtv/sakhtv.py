# -*- coding: utf-8 -*-
import urllib, urllib2, json
import xbmc, xbmcaddon, xbmcgui, xbmcplugin

try:
	from hashlib import md5 as md5
except:
	import md5

try:
	from hashlib import sha as sha
except:
	import sha

def getHTML(url):
	timeout = 10
	try:
		conn = urllib2.urlopen(url, None, timeout)
	except:
		xbmc.executebuiltin('Notification(%s,%s)' % (getString(32014).encode('utf-8'), getString(32019).encode('utf-8')))
		raise SystemExit(1)
	else:
		html = conn.read()
		if conn.getcode() != 200:
			xbmc.executebuiltin('Notification(%s,%s)' % (getString(32014).encode('utf-8'), getString(32019).encode('utf-8')))
			raise SystemExit(1)
		conn.close()
	return json.loads(html)
	
def get_params():
	param=[]
	paramstring=sys.argv[2]
	if len(paramstring)>=2:
		params=sys.argv[2]
		cleanedparams=params.replace('?','')
		if (params[len(params)-1]=='/'):
			params=params[0:len(params)-2]
		pairsofparams=cleanedparams.split('&')
		param={}
		for i in range(len(pairsofparams)):
			splitparams={}
			splitparams=pairsofparams[i].split('=')
			if (len(splitparams))==2:
				param[splitparams[0]]=splitparams[1]
	return param

def get_param(dict, param):
	try:
		return dict[param].encode('utf-8')
	except:
		return ""
	
def f_md5(str):
	try:
		rez = md5(str)
	except:
		rez = md5.md5(str)
	return rez.hexdigest()

def f_sha(str):
	try:
		rez = sha(str)
	except:
		rez = sha.sha(str)
	return rez.hexdigest()

def getString(string_id):
	return addon.getLocalizedString(string_id)
	
def dump(obj):
	newobj=obj
	if '__dict__' in dir(obj):
		newobj=obj.__dict__
		if ' object at ' in str(obj) and not newobj.has_key('__type__'):
			newobj['__type__']=str(obj)
		for attr in newobj:
			newobj[attr]=dump(newobj[attr])
	return newobj

addon      =   xbmcaddon.Addon(id="plugin.video.sakhtv")
addon_id   =   int(sys.argv[1])
addon_url  =   sys.argv[0]
addon_icon =   addon.getAddonInfo('icon') 

#xbmc.log("parameters: %s" % dump(get_params()), level=xbmc.LOGNOTICE)

user   = addon.getSetting('user')
token  = addon.getSetting('token')
amount = int(addon.getSetting('amount'));

params = get_params()
# Вызов плагина без параметров
if params == []: 
	#Проверка IP
	if getHTML('https://api.sakh.tv/v2/auth.iptest/')['result'] != True:
		dialog = xbmcgui.Dialog()
		ok = dialog.ok(getString(32014), getString(32015)) # "Error" "Your IP-address is not in range of Sakhalin."
		raise SystemExit(1)
		
	password   =   addon.getSetting('password');
	if user == "":
		addon.openSettings()
		raise SystemExit(1)

	#Генерирование токена из пароля
	if password != '':
		addon.setSetting('token', f_md5(user.lower() + ':' + f_sha(password)))
		addon.setSetting('password', '')

	#Проверка авторизации
	if getHTML('https://api.sakh.tv/v2/auth.check/?user=%s&token=%s' % (user, token))['result'] != "ok":
		dialog = xbmcgui.Dialog()
		dialog.ok(getString(32014), getString(32016)) # "Error" "Authentification error. Fill in correct credentials."
		addon.openSettings()
		raise SystemExit(1)
	
	# Избранное
	list_item = xbmcgui.ListItem('[COLOR=FFFF2222]%s[/COLOR]' % getString(32017), iconImage=addon_icon) # "Favorites"
	xbmcplugin.addDirectoryItem(addon_id, addon_url + '?mode=favorites&page=0&amount=%s&' % amount, list_item, isFolder=True)
	
	# По алфавиту
	list_item = xbmcgui.ListItem(getString(32020), iconImage=addon_icon) # "Alphabet order"
	xbmcplugin.addDirectoryItem(addon_id, addon_url + '?mode=abc&page=0&amount=%s&' % amount, list_item, isFolder=True)

	# Популярные
	list_item = xbmcgui.ListItem(getString(32021), iconImage=addon_icon) # "Popular"
	xbmcplugin.addDirectoryItem(addon_id, addon_url + '?mode=pop&page=0&amount=%s&' % amount, list_item, isFolder=True)
	
	# Новые
	list_item = xbmcgui.ListItem(getString(32022), iconImage=addon_icon) # "New"
	xbmcplugin.addDirectoryItem(addon_id, addon_url + '?mode=new&page=0&amount=%s&' % amount, list_item, isFolder=True)
	
elif params['mode'] in ['abc', 'pop', 'new', 'favorites']:
	xbmcplugin.setContent(addon_id, 'TVShows')
	if params['mode'] == 'favorites':
		series = getHTML('https://api.sakh.tv/v2/favorites.get/?user=%s&token=%s&page=%s&amount=%s' % (user, token, params['page'], amount))
	else:
		series = getHTML('https://api.sakh.tv/v2/serials.get/?user=%s&token=%s&page=%s&amount=%s&sort=%s' % (user, token, params['page'], amount, params['mode']))
	
	if int(params["page"]) > 0:
		list_item = xbmcgui.ListItem('[COLOR=FF8888FF]%s[/COLOR]' % getString(32024), iconImage=None) # "Previous page"
		xbmcplugin.addDirectoryItem(addon_id, addon_url + '?mode=%s&page=%s&amount=%s&' % (params['mode'], int(params["page"])-1, amount), list_item, isFolder=True)
	for i in series['data']:
		fullName = i['name'].encode('utf-8')
		if i['ename'] != '':
			fullName = fullName + ('[COLOR=FF444444] - ' + i["ename"] + '[/COLOR]').encode('utf-8')
		list_item = xbmcgui.ListItem("%s" % fullName, iconImage=addon_icon)
		list_item.setInfo ("video", {"Genre": i['genre'].encode('utf-8'), 'Episode' : i['episodes_amount'], 'Plot': i['about'].encode('utf-8'), 'TVShowTitle':i['ename'], 'Year': i['year'], 'Rating': i['rating']})
		list_item.setArt({'thumb': i['poster'], 'fanart': i['backdrop'], 'poster': i['poster']})
		xbmcplugin.addDirectoryItem(addon_id, addon_url + '?mode=seasons&serial_id=%s' % i['id'], list_item, isFolder=True)
	#xbmc.log('%s - %s - %s' % (int(series['total']), (int(params["page"]) + 1), amount), xbmc.LOGNOTICE)
	if int(series['total']) > (int(params["page"]) + 1) * amount :
		list_item = xbmcgui.ListItem('[COLOR=FF8888FF]%s[/COLOR]' % getString(32023), iconImage=None) # "Next page"
		xbmcplugin.addDirectoryItem(addon_id, addon_url + '?mode=%s&page=%s&amount=%s&' % (params['mode'], int(params["page"])+1, amount), list_item, isFolder=True)
		
elif params['mode'] == "seasons":
	xbmcplugin.setContent(addon_id, 'Seasons')
	series = getHTML('https://api.sakh.tv/v2/seasons.get/?user=%s&token=%s&serial_id=%s&page=&amount=' % (user, token, params['serial_id']))
	for i in series["data"]:
		list_item = xbmcgui.ListItem("%s %s" % (i['index'], getString(32025)))
		#list_item.setInfo ("video", {"Genre": i['genre'].encode('utf-8'), 'Episode' : i['episodes_amount'], 'Plot': i['about'].encode('utf-8'), 'TVShowTitle':'TVShowTitle', 'Year': i['year']}) # , 
		#list_item.setArt({'thumb': i['poster'], 'fanart': i['backdrop']})
		xbmcplugin.addDirectoryItem(addon_id, addon_url + '?mode=episodes&season_id=%s&season=%s' % (i['id'], i['index']), list_item, isFolder=True)
		
elif params['mode'] == "episodes":
	xbmcplugin.setContent(addon_id, 'Episodes')
	series = getHTML('https://api.sakh.tv/v2/files.get/?user=%s&token=%s&season_id=%s&page=0&amount=%s&format=mp4' % (user, token, params['season_id'], amount))
	for i in series["data"]:
		list_item = xbmcgui.ListItem("%s" % (i['index'] + "x" + params['season'] + " " + i['name']))
		list_item.setInfo ("video", {"Episode": i['index'], 'TVShowTitle':'TVShowTitle', 'Aired': i['date']})
		list_item.setArt({'thumb': 'https://sakh.tv/' + i['preview']})
		xbmcplugin.addDirectoryItem(addon_id, i['files'][1]['src'], list_item, isFolder=False)

xbmcplugin.endOfDirectory(addon_id, cacheToDisc=True)