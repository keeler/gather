from bs4 import BeautifulSoup
import urllib
import re
import os
from collections import defaultdict

def scrapePage( multiverseId ):
	soup = BeautifulSoup( urllib.urlopen( 'http://gatherer.wizards.com/Pages/Card/Details.aspx?multiverseid=' + multiverseId ) )
	card = defaultdict( str )

	# Get name.
	nametag = soup.find( 'div', { 'id' : 'ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_nameRow', 'class' : 'row' } )
	if nametag:
		card['name'] = nametag.findChildren( 'div', { 'class' : 'value' } )[0].text.strip()

	# Get mana cost.
	manatag = soup.find( 'div', { 'id' : 'ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_manaRow', 'class' : 'row' } )
	if manatag:
		symbols = manatag.findChildren( 'div', { 'class' : 'value' } )[0].findChildren( 'img' )
		for symbol in symbols:
			m = re.search( '\&name=([\dA-Z]+)\&', symbol['src'] )
			if m:
				if 'P' in m.groups()[0]:
					card['mana'] += ( '{' + m.groups()[0] + '}' )
				else:
					card['mana'] += ( '{' + '/'.join( list( m.groups()[0] ) ) + '}' )

	# Get converted mana cost.
	cmctag = soup.find( 'div', { 'id' : 'ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_cmcRow', 'class' : 'row' } )
	if cmctag:
		card['cmc'] = cmctag.findChildren( 'div', { 'class' : 'value' } )[0].text.strip()

	# Get types.
	typetag = soup.find( 'div', { 'id' : 'ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_typeRow', 'class' : 'row' } )
	if typetag:
		typestring = typetag.findChildren( 'div', { 'class' : 'value' } )[0].text.strip()
		types = re.compile( ur'\u2014', re.UNICODE ).split( typestring )
		for t in types[0].split( ' ' ):
			if t in ['Basic', 'Legendary', 'Snow', 'World']:
				card['supertype'] += ( t + ' ' )
			elif t in ['Artifact', 'Creature', 'Enchantment', 'Land', 'Planeswalker', 'Tribal', 'Instant', 'Sorcery']:
				card['type'] += ( t + ' ' )
			elif t:
				print 'Unknown type:', t, 'multiverseId =', multiverseId
		card['supertype'] = card['supertype'].strip()
		card['type'] = card['type'].strip()
		if len( types ) > 1:
			card['subtype'] = types[1].strip()

	# Get card's rule text.
	texttag = soup.find( 'div', { 'id' : 'ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_textRow', 'class' : 'row' } )
	if texttag:
		rules = texttag.findChildren( 'div', { 'class' : 'value' } )[0].findChildren( 'div', { 'class' : 'cardtextbox' } )
		for r in rules:
			print unicode( r )

	return card


def saveMasterList():
	soup = BeautifulSoup( urllib.urlopen( 'http://gatherer.wizards.com/Pages/Search/Default.aspx?page=0&name=+[]' ) )

ids = [ '218043', '159408', '153471', '73935' ]
for i in ids:
	c = scrapePage( i )
	print '=' * 80
	print c['name']
	print c['mana']
	print c['cmc']
	print c['supertype']
	print c['type']
	print c['subtype']
	print c['rule']
