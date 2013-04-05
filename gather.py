from bs4 import BeautifulSoup
import urllib
import re
import os
from collections import defaultdict

def getName( soup ):
	nametag = soup.find( 'div', { 'id' : 'ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_nameRow', 'class' : 'row' } )
	if nametag:
		return nametag.findChildren( 'div', { 'class' : 'value' } )[0].text.strip()
	else:
		return ''


def getManaCost( soup ):
	manatag = soup.find( 'div', { 'id' : 'ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_manaRow', 'class' : 'row' } )
	manastring = ''
	if manatag:
		symbols = manatag.findChildren( 'div', { 'class' : 'value' } )[0].findChildren( 'img' )
		for symbol in symbols:
			m = re.search( '\&name=([\dA-Z]+)\&', symbol['src'] )
			if m:
				if 'P' in m.groups()[0]:
					manastring += ( '{' + m.groups()[0] + '}' )
				else:
					manastring += ( '{' + '/'.join( list( m.groups()[0] ) ) + '}' )
	return manastring


def getConvertedManaCost( soup ):
	cmctag = soup.find( 'div', { 'id' : 'ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_cmcRow', 'class' : 'row' } )
	if cmctag:
		return cmctag.findChildren( 'div', { 'class' : 'value' } )[0].text.strip()
	else:
		return ''


# Returns 3-tuple of strings, one for supertypes, one for types, and one for subtypes.
def getTypes( soup ):
	typetag = soup.find( 'div', { 'id' : 'ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_typeRow', 'class' : 'row' } )

	supertypes = ''
	types = ''
	subtypes = ''
	if typetag:
		typestring = typetag.findChildren( 'div', { 'class' : 'value' } )[0].text.strip()
		typelist = re.compile( ur'\u2014', re.UNICODE ).split( typestring )
		for t in typelist[0].split( ' ' ):
			if t in ['Basic', 'Legendary', 'Snow', 'World']:
				supertypes += ( t + ' ' )
			elif t in ['Artifact', 'Creature', 'Enchantment', 'Land', 'Planeswalker', 'Tribal', 'Instant', 'Sorcery']:
				types += ( t + ' ' )
			elif t:
				print 'Unknown type:', t, 'multiverseId =', multiverseId
		supertypes = supertypes.strip()
		types = types.strip()
		if len( typelist ) > 1:
			subtypes = typelist[1].strip()

	return ( supertypes, types, subtypes )


def getRuleText( soup ):
	texttag = soup.find( 'div', { 'id' : 'ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_textRow', 'class' : 'row' } )
	if texttag:
		rules = texttag.findChildren( 'div', { 'class' : 'value' } )[0].findChildren( 'div', { 'class' : 'cardtextbox' } )
		cardlines = []
		for r in rules:
			rulestring = unicode( r )
			symbols = re.findall( '<img.*?\&amp\;name=([\da-zA-Z]+)\&amp\;.*?\/>', rulestring )
			if symbols:
				for i in range( len( symbols ) ):
					if 'tap' in symbols[i]:
						symbols[i] = '{T}'
					elif 'P' in symbols[i]:
						symbols[i] = '{' + symbols[i] + '}'
					else:
						symbols[i] = '{' + '/'.join( list( symbols[i] ) ) + '}'

				for s in symbols:
					rulestring = re.sub( '<img.*?/>', s, rulestring, 1 )

			rulestring = re.sub( '<.?div.*?>', '', rulestring )
			rulestring = re.sub( '<.?i>', '', rulestring )
			cardlines.append( rulestring )
	
	return '<br>'.join( cardlines )

# Returns power, toughness as tuple.
def getPowerToughness( soup ):
	pttag = soup.find( 'div', { 'id' : 'ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_ptRow', 'class' : 'row' } )
	if pttag:
		pt = pttag.findChildren( 'div', { 'class' : 'value' } )[0].text.strip().split( '/' )
		return ( pt[0].strip(), pt[1].strip() )
	else:
		return ( '', '' )


def getRarity( soup ):
	raritytag = soup.find( 'div', { 'id' : 'ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_rarityRow', 'class' : 'row' } )
	if raritytag:
		return raritytag.findChildren( 'div', { 'class' : 'value' } )[0].text.strip()
	else:
		return ''


def getArtist( soup ):
	artisttag = soup.find( 'div', { 'id' : 'ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_artistRow', 'class' : 'row' } )
	if artisttag:
		return artisttag.findChildren( 'div', { 'class' : 'value' } )[0].text.strip()
	else:
		return ''


def getSetName( soup ):
	settag = soup.find( 'div', { 'id' : 'ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_setRow', 'class' : 'row' } )
	if settag:
		return settag.findChildren( 'div', { 'class' : 'value' } )[0].text.strip()
	else:
		return ''


# Cards from early sets may not have a collector number, just so's ya know.
def getCollectorNumber( soup ):
	cntag = soup.find( 'div', { 'id' : 'ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_numberRow', 'class' : 'row' } )
	if cntag:
		return cntag.findChildren( 'div', { 'class' : 'value' } )[0].text.strip()
	else:
		return ''


def getFlavorText( soup ):
	flavortag = soup.find( 'div', { 'id' : 'ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_flavorRow', 'class' : 'row' } )
	if flavortag:
		flavorlines = flavortag.findChildren( 'div', { 'class' : 'value' } )[0].findChildren( 'div', { 'class' : 'cardtextbox' } )
		p = re.compile( ur'\u2014', re.UNICODE )
		flavortext = [] 
		for flavor in flavorlines:
			flavortext.append( p.sub( '--', flavor.text ).strip() )
		return '<br>'.join( flavortext )
	else:
		return ''


# Cards can be printed over many different sets, e.g. Naturalize. Make a list
# of these editions, where each list item is a tuple of the set name, collector
# number for that set, flavor text, and artist.
def getEditionsList( soup ):
	editions = []
	# First get the information on this page, then crawl to the pages for the other sets.
	editions.append( ( getSetName( soup ), getCollectorNumber( soup ), getFlavorText( soup ), getArtist( soup ) ) )

	othertag = soup.find( 'div', { 'id' : 'ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_otherSetsRow', 'class' : 'row' } )
	if othertag:
		setlinks = othertag.findChildren( 'div', { 'class' : 'value' } )[0].find_all( 'a' )
		for setlink in setlinks:
			m = re.search( '(\d+)$', setlink['href'] )
			if m:
				othersoup = BeautifulSoup( urllib.urlopen( 'http://gatherer.wizards.com/Pages/Card/Details.aspx?multiverseid=' + m.groups()[0] ) )
				editions.append( ( getSetName( othersoup ), getCollectorNumber( othersoup ), getFlavorText( othersoup ), getArtist( othersoup ) ) )

	return editions


def scrapePage( multiverseId ):
	soup = BeautifulSoup( urllib.urlopen( 'http://gatherer.wizards.com/Pages/Card/Details.aspx?multiverseid=' + multiverseId ) )
	card = defaultdict( str )

	card['name'] = getName( soup )
	card['mana'] = getManaCost( soup )
	card['cmc'] = getConvertedManaCost( soup )
	card['supertype'], card['type'], card['subtype'] = getTypes( soup )
	card['rules'] = getRuleText( soup )
	card['power'], card['toughness'] = getPowerToughness( soup )
	card['rarity'] = getRarity( soup )
	card['editions'] = getEditionsList( soup )

	return card

def saveMasterList():
	soup = BeautifulSoup( urllib.urlopen( 'http://gatherer.wizards.com/Pages/Search/Default.aspx?page=0&name=+[]' ) )

ids = [ '218043', '159408', '153471', '73935', '201563', '366303' ]
for i in ids:
	c = scrapePage( i )
	print '=' * 80
	print c['name']
	print c['mana']
	print c['cmc']
	print c['supertype']
	print c['type']
	print c['subtype']
	print c['rules']
	print c['power']
	print c['toughness']
	print c['rarity']
	print c['editions']

