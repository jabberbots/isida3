#!/usr/bin/python
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------- #
#                                                                             #
#    Plugin for iSida Jabber Bot                                              #
#    Copyright (C) 2012 diSabler <dsy@dsy.name>                               #
#                                                                             #
#    This program is free software: you can redistribute it and/or modify     #
#    it under the terms of the GNU General Public License as published by     #
#    the Free Software Foundation, either version 3 of the License, or        #
#    (at your option) any later version.                                      #
#                                                                             #
#    This program is distributed in the hope that it will be useful,          #
#    but WITHOUT ANY WARRANTY; without even the implied warranty of           #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the            #
#    GNU General Public License for more details.                             #
#                                                                             #
#    You should have received a copy of the GNU General Public License        #
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.    #
#                                                                             #
# --------------------------------------------------------------------------- #

acl_acts = ['msg','message','prs','prs_change','prs_join','presence','presence_change','presence_join',
			'role','role_change','role_join','affiliation','affiliation_change','affiliation_join',
			'nick','nick_change','nick_join','all','all_change','all_join','jid','jidfull','res','age','ver','version']
acl_actions = ['show','del'] + acl_acts

acl_ver_tmp = {}

def acl_show(jid,text):
	a = cur_execute_fetchall('select * from acl where jid=%s and action ilike %s',(jid,text))
	if len(a):
		msg = L('Acl:')
		for tmp in a:
			if text == '%': t4 = tmp[4].replace('\n',' // ')
			else: t4 = tmp[4]
			if tmp[5]: st,tp = '\n[%s] %s %s %s -> %s', (time.ctime(float(tmp[5])),) + tmp[1:4] + (t4,)
			else: st,tp = '\n%s %s %s -> %s', tmp[1:4] + (t4,)
			msg += st % tp
	else: msg = L('Acl not found')
	return msg

def acl_add_del(jid,text,flag):
	global conn
	time_mass,atime = {'s':1,'m':60,'h':3600,'d':86400,'w':604800,'M':2592000,'y':31536000},0
	silent = False
	try:
		while text[0][0] == '/':
			if text[0] == '/silent': silent = True
			else:
				try: atime = int(time.time()) + int(text[0][1:-1]) * time_mass[text[0][-1:]]
				except: return L('Time format error!')
			text = text[1:]
	except: return L('Error in parameters. Read the help about command.')
	ttext = ' '.join(text)
	if operator.xor(ttext.count('${EXP}') <= 1,ttext.count('${/EXP}') <= 1) and flag: return L('Error in parameters. Read the help about command.')
	elif ttext.find('${EXP}',ttext.find('${/EXP}')) > 0 and flag: return L('Error in parameters. Read the help about command.')
	elif '${EXP}' in ttext and '${/EXP}' in ttext:
		try: re.compile(ttext.split('${EXP}',1)[1].split('${/EXP}',1)[0].replace('%20','\ ').replace('*','*?'))
		except: return L('Error in RegExp!')
	acl_cmd = text[0].lower()
	text = text[1:]
	if not acl_cmd in acl_acts: msg = L('Items: %s') % ', '.join(acl_acts)
	else:
		try:
			if text[0].lower() in ['sub','!sub','exp','!exp','cexp','!cexp','=','!=','<','>','<=','>=']: acl_sub_act,text = text[0].lower(),text[1:]
			else: acl_sub_act = '='
		except: return L('Error in parameters. Read the help about command.')
		if acl_cmd != 'age' and acl_sub_act in ['<','>','<=','>=']: return L('Error in parameters. Read the help about command.')
		if acl_sub_act in ['=','!=','sub','!sub']: text[0] = text[0].replace('%20',' ')
		else: text[0] = text[0].replace('%20','\ ')
		if acl_sub_act in ['exp','!exp','cexp','!cexp']:
			try: re.compile(text[0].replace('*','*?'))
			except: return L('Error in RegExp!')
		if flag and len(text) >= 2:
			no_command = True
			for tmp in comms:
				if tmp[1] == text[1]:
					no_command = False
					break
			if no_command: return L('Unknown command: %s') % text[1]
		tmp = cur_execute_fetchall('select * from acl where jid=%s and action=%s and type=%s and text=%s',(jid,acl_cmd, acl_sub_act, text[0]))
		if tmp:
			cur_execute('delete from acl where jid=%s and action=%s and type=%s and text=%s',(jid,acl_cmd, acl_sub_act, text[0]))
			msg = [L('Removed:'),L('Updated:')][flag]
		else: msg = [L('Not found:'),L('Added:')][flag]
		if flag: cur_execute('insert into acl values (%s,%s,%s,%s,%s,%s)', (jid, acl_cmd, acl_sub_act, text[0], ' '.join(text[1:]).replace('%20','\ '), atime))
		if atime: msg += ' [%s] %s %s %s -> %s' % (time.ctime(atime),acl_cmd, acl_sub_act, text[0], ' '.join(text[1:]).replace('%20','\ ').replace('\n',' // '))
		else: msg += ' %s %s %s -> %s' % (acl_cmd, acl_sub_act, text[0], ' '.join(text[1:]).replace('%20','\ ').replace('\n',' // '))
		if not reduce_spaces_all(msg).split('->',1)[1]: msg = msg.split('->',1)[0]
		if flag and acl_cmd not in['msg','message']:
			mb = [t[1:] for t in megabase if t[0] == jid and getRoom(t[4]) != getRoom(Settings['jid'])]
			a = [(acl_cmd, acl_sub_act, text[0], ' '.join(text[1:]).replace('%20','\ '), 0)]				
			was_joined = True
			for t in mb:
				room, realjid, nick = jid, t[3], t[0]
				mass = cur_execute_fetchone('select message from age where jid=%s and room=%s and nick=%s',(getRoom(realjid),room,nick))[0].split('\n',4)
				mass = (mass[4], mass[0], mass[1])
				acl_selector(a,room,realjid,nick,mass,was_joined)
	if silent: return L('done')
	else: return msg

def acl_add(jid,text): return acl_add_del(jid,text,True)

def acl_del(jid,text): return acl_add_del(jid,text,False)

def muc_acl(type, jid, nick, text):
	text = text.replace('\ ','%20').split(' ')
	if len(text) >= 3 and text[2] == '->': text[2] = ''
	elif len(text) >= 4 and text[3] == '->': text[3] = ''
	elif text[0].lower() == 'del' and len(text) >= 5 and text[4] == '->': text[4] = ''
	while '' in text: text.remove('')
	if len(text): acl_cmd = text[0].lower()
	else: acl_cmd = '!'
	if not acl_cmd in acl_actions and acl_cmd[0] != '/': msg = L('Items: %s') % ', '.join(acl_actions)
	elif acl_cmd == 'show':
		try: t = text[1]
		except: t = '%'
		msg = acl_show(jid,t)
	elif acl_cmd == 'del': msg = acl_del(jid,text[1:])
	else: msg = acl_add(jid,text)
	send_msg(type, jid, nick, msg)

def acl_action(cmd,nick,jid,room,text):
	global last_command
	if len(last_command):
		if last_command[6] == Settings['jid']: last_command = []
	cmd = cmd.replace('${NICK}',nick).replace('${JID}',jid).replace('${SERVER}',getServer(jid))
	if text and '${EXP}' in cmd and '${/EXP}' in cmd:
		regex = cmd.split('${EXP}',1)[1].split('${/EXP}',1)[0]
		mt = re.findall(regex, text, re.S+re.U+re.I)
		if mt != []: txt = ''.join(mt[0])
		else: txt = ''
		cmd = cmd.split('${EXP}',1)[0] + txt + cmd.split('${/EXP}',1)[1]
	tmppos = arr_semi_find(confbase, room)
	if tmppos == -1: nowname = Settings['nickname']
	else:
		nowname = getResourse(confbase[tmppos])
		if nowname == '': nowname = Settings['nickname']
	return com_parser(7, nowname, 'groupchat', room, nick, cmd, Settings['jid'])

def acl_message(room,jid,nick,type,text):
	global conn
	#if not no_comm: return
	if get_level(room,nick)[0] < 0: return
	if getRoom(jid) == getRoom(Settings['jid']): return
	a = cur_execute_fetchall('select action,type,text,command,time from acl where jid=%s and (action=%s or action=%s or action ilike %s)',(room,'msg','message','all%'))
	no_comm = True
	if a:
		for tmp in a:
			if tmp[4] <= time.time() and tmp[4]: 
				cur_execute('delete from acl where jid=%s and action=%s and type=%s and text=%s',(room,tmp[0],tmp[1],tmp[2]))
			
			was_match = False
			if tmp[1].endswith('exp'):
				if tmp[1].startswith('!') and not bool(re.findall(tmp[2].replace('*','*?'),text,re.I+re.S+re.U)): was_match = True
				elif bool(re.findall(tmp[2].replace('*','*?'),text,re.I+re.S+re.U)): was_match = True
			elif tmp[1].endswith('cexp'):
				if tmp[1].startswith('!') and not bool(re.findall(tmp[2].replace('*','*?'),text,re.S+re.U)): was_match = True
				elif bool(re.findall(tmp[2].replace('*','*?'),text,re.S+re.U)): was_match = True
			elif tmp[1].endswith('sub'):
				if tmp[1].startswith('!') and not bool(tmp[2].lower() in text.lower()): was_match = True
				elif bool(tmp[2].lower() in text.lower()): was_match = True
			elif tmp[1].endswith('='):
				if tmp[1].startswith('!') and bool(text.lower() != tmp[2].lower()): was_match = True
				elif bool(text.lower() == tmp[2].lower()): was_match = True
			if was_match:
				no_comm = acl_action(tmp[3],nick,jid,room,text)
				break

	return not no_comm

def bool_compare(a,b,c):
	a,c = int(a),int(c)
	return (b == '=' and a == c)\
		or (b == '<' and a < c)\
		or (b == '>' and a > c)\
		or (b == '<=' and a >= c)\
		or (b == '>=' and a >= c)
	
def acl_presence(room,jid,nick,type,mass):
	global iq_request,acl_ver_tmp
	#if get_level(room,nick)[0] < 0: return
	if getRoom(jid) == getRoom(Settings['jid']): return
	was_joined = not mass[7] or is_start
	if type == 'error': return
	elif type == 'unavailable':
		try: acl_ver_tmp.pop('%s/%s' % (room,nick))
		except: pass
		return
	# actions only on joins
	#if was_joined: return
	a = cur_execute_fetchall('select action,type,text,command,time from acl where jid=%s and (action ilike %s or action ilike %s or action ilike %s or action ilike %s or action ilike %s or action ilike %s or action=%s or action=%s or action=%s or action=%s or action=%s or action=%s)',(room,'prs%','presence%','nick%','all%','role%','affiliation%','jid','jidfull','res','age','ver','version'))
	if a: acl_selector(a,room,jid,nick,mass,was_joined)

def acl_selector(a,room,jid,nick,mass,was_joined):
	global iq_request,acl_ver_tmp
	for tmp in a:
		if tmp[0] == 'age':
			past_age = cur_execute_fetchone('select sum(age) from age where room=%s and jid=%s and status=%s',(room,getRoom(jid),1))
			now_age  = cur_execute_fetchone('select time,age from age where room=%s and jid=%s and status=%s',(room,getRoom(jid),0))
			r_age = 0
			if past_age or now_age:
				try: r_age += past_age[0]
				except: pass
				try: r_age += int(time.time())-now_age[0]+now_age[1]
				except: pass
			break

	for tmp in a:
		if tmp[0] in ['ver','version'] and was_joined:
			try: r_ver = acl_ver_tmp['%s/%s' % (room,nick)]
			except:
				iqid,who = get_id(), '%s/%s' % (room,nick)
				i = Node('iq', {'id': iqid, 'type': 'get', 'to':who}, payload = [Node('query', {'xmlns': NS_VERSION},[])])
				iq_request[iqid]=(time.time(),acl_version_async,[a, nick, jid, room, mass[0]])
				sender(i)
				r_ver = None
				pprint('*** ACL version request for %s/%s' % (room,nick),'purple')
				break

	for tmp in a:
		itm = ''
		if tmp[4] <= time.time() and tmp[4]:
			cur_execute('delete from acl where jid=%s and action=%s and type=%s and text=%s',(room,tmp[0],tmp[1],tmp[2]))
		if tmp[0].split('_')[0] in ['presence','prs'] and (('_join' in tmp[0] and was_joined) or ('_change' in tmp[0] and not was_joined) or ('_join' not in tmp[0] and '_change' not in tmp[0])): itm = mass[0]
		elif tmp[0].split('_')[0] == 'nick' and (('_join' in tmp[0] and was_joined) or ('_change' in tmp[0] and not was_joined) or ('_join' not in tmp[0] and '_change' not in tmp[0])): itm = nick
		elif tmp[0].split('_')[0] == 'role' and (('_join' in tmp[0] and was_joined) or ('_change' in tmp[0] and not was_joined) or ('_join' not in tmp[0] and '_change' not in tmp[0])): itm = mass[1]
		elif tmp[0].split('_')[0] == 'affiliation' and (('_join' in tmp[0] and was_joined) or ('_change' in tmp[0] and not was_joined) or ('_join' not in tmp[0] and '_change' not in tmp[0])): itm = mass[2]
		elif tmp[0].split('_')[0] == 'all' and (('_join' in tmp[0] and was_joined) or ('_change' in tmp[0] and not was_joined) or ('_join' not in tmp[0] and '_change' not in tmp[0])): itm = '|'.join((jid,nick,mass[0],mass[1],mass[2]))
		elif tmp[0] == 'jid' and was_joined: itm = getRoom(jid)
		elif tmp[0] == 'jidfull' and was_joined: itm = jid
		elif tmp[0] == 'res' and was_joined: itm = getResourse(jid)
		elif tmp[0] in ['ver','version'] and was_joined and r_ver: itm = r_ver
		elif tmp[0] == 'age' and was_joined and bool_compare(r_age,tmp[1],tmp[2]):
			acl_action(tmp[3],nick,jid,room,None)
			break
		if itm:
			was_match = False
			if tmp[1].endswith('exp'):
				if tmp[1].startswith('!') and not bool(re.findall(tmp[2].replace('*','*?'),itm,re.I+re.S+re.U)): was_match = True
				elif bool(re.findall(tmp[2].replace('*','*?'),itm,re.I+re.S+re.U)): was_match = True
			elif tmp[1].endswith('cexp'):
				if tmp[1].startswith('!') and not bool(re.findall(tmp[2].replace('*','*?'),itm,re.S+re.U)): was_match = True
				elif bool(re.findall(tmp[2].replace('*','*?'),itm,re.S+re.U)): was_match = True
			elif tmp[1].endswith('sub'):
				if tmp[1].startswith('!') and bool(tmp[2].lower() not in itm.lower()): was_match = True
				elif bool(tmp[2].lower() in itm.lower()): was_match = True
			elif tmp[1].endswith('='):
				if tmp[1].startswith('!') and not bool(itm.lower() == tmp[2].lower()) or not (tmp[0] == 'all' and bool(tmp[2].lower() in (jid.lower(),nick.lower(),mass[0].lower()))): was_match = True
				elif bool(itm.lower() == tmp[2].lower()) or (tmp[0] == 'all' and bool(tmp[2].lower() in (jid.lower(),nick.lower(),mass[0].lower()))): was_match = True
			if was_match:
				acl_action(tmp[3],nick,jid,room,None)
				break

def acl_version_async(a, nick, jid, room, mass, is_answ):
	global acl_ver_tmp
	isa = is_answ[1]
	if len(isa) == 3: itm = '%s %s // %s' % isa
	else: itm = ' '.join(isa)
	acl_ver_tmp['%s/%s' % (room,nick)] = itm.replace('\r','[LF]').replace('\n','[CR]').replace('\t','[TAB]')
	for tmp in a:
		if tmp[0] in ['ver','version']:			
			was_match = False
			if tmp[1].endswith('exp'):
				if tmp[1].startswith('!') and not bool(re.findall(tmp[2].replace('*','*?'),itm,re.I+re.S+re.U)): was_match = True
				elif bool(re.findall(tmp[2].replace('*','*?'),itm,re.I+re.S+re.U)): was_match = True
			elif tmp[1].endswith('cexp'):
				if tmp[1].startswith('!') and not bool(re.findall(tmp[2].replace('*','*?'),itm,re.S+re.U)): was_match = True
				elif bool(re.findall(tmp[2].replace('*','*?'),itm,re.S+re.U)): was_match = True
			elif tmp[1].endswith('sub'):
				if tmp[1].startswith('!') and not bool(tmp[2].lower() in itm.lower()): was_match = True
				elif bool(tmp[2].lower() in itm.lower()): was_match = True
			elif tmp[1].endswith('='):
				if tmp[1].startswith('!') and not bool(itm.lower() == tmp[2].lower()) or not (tmp[0] == 'all' and bool(tmp[2].lower() in (jid.lower(),nick.lower(),'\n'.join(mass).lower()))): was_match = True
				elif bool(itm.lower() == tmp[2].lower()) or (tmp[0] == 'all' and bool(tmp[2].lower() in (jid.lower(),nick.lower(),'\n'.join(mass).lower()))): was_match = True
			if was_match: acl_action(tmp[3],nick,jid,room,None)

global execute, presence_control, message_act_control

presence_control = [acl_presence]
message_act_control = [acl_message]

execute = [(7, 'acl', muc_acl, 2, L('Actions list.\nacl show - show list\nacl del [/silent] item - remove item from list\nacl [/time] [/silent] msg|message|prs|presence|role|affiliation|nick|jid|jidfull|res|age|ver|version|all [sub|exp|cexp] pattern command - execute command by condition\nallowed variables in commands: ${NICK}, ${JID}, ${SERVER}, ${EXP} and ${/EXP}\nsub = substring, exp = regular expression, cexp = case sensitive regular expression\ntime format is /number+identificator. s = sec, m = min, d = day, w = week, M = month, y = year. only one identificator allowed!'))]
