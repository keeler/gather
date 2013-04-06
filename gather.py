from bs4 import BeautifulSoup
import urllib
import re
import os
from collections import defaultdict

def getName( soup, doubleSided = False, desiredSide = 'a' ):
	nametag = ''
	if doubleSided:
		if desiredSide == 'a':
			nametag = soup.find( 'div', { 'id' : 'ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_ctl07_nameRow', 'class' : 'row' } )
		elif desiredSide == 'b':
			nametag = soup.find( 'div', { 'id' : 'ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_ctl08_nameRow', 'class' : 'row' } )
	else:
		nametag = soup.find( 'div', { 'id' : 'ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_nameRow', 'class' : 'row' } )

	if nametag:
		return nametag.findChildren( 'div', { 'class' : 'value' } )[0].text.strip()
	else:
		return ''


def getManaCost( soup, doubleSided = False, desiredSide = 'a' ):
	manatag = ''
	if doubleSided:
		if desiredSide == 'a':
			manatag = soup.find( 'div', { 'id' : 'ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_ctl07_manaRow', 'class' : 'row' } )
		elif desiredSide == 'b':
			manatag = soup.find( 'div', { 'id' : 'ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_ctl08_manaRow', 'class' : 'row' } )
	else:
		manatag = soup.find( 'div', { 'id' : 'ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_manaRow', 'class' : 'row' } )

	manastring = ''
	if manatag:
		symbols = manatag.findChildren( 'div', { 'class' : 'value' } )[0].findChildren( 'img' )
		for symbol in symbols:
			m = re.search( '\&name=([\dA-Z]+)\&', symbol['src'] )
			if m:
				if 'snow' in m.groups()[0]:
					manastring += '{S}'
				elif 'P' in m.groups()[0]:
					manastring += ( '{' + m.groups()[0] + '}' )
				else:
					manastring += ( '{' + '/'.join( list( m.groups()[0] ) ) + '}' )
	return manastring


def getConvertedManaCost( soup, doubleSided = False, desiredSide = 'a' ):
	cmctag = ''
	if doubleSided:
		if desiredSide == 'a':
			cmctag = soup.find( 'div', { 'id' : 'ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_ctl07_cmcRow', 'class' : 'row' } )
		elif desiredSide == 'b':
			cmctag = soup.find( 'div', { 'id' : 'ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_ctl08_cmcRow', 'class' : 'row' } )
	else:
		cmctag = soup.find( 'div', { 'id' : 'ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_cmcRow', 'class' : 'row' } )

	if cmctag:
		return cmctag.findChildren( 'div', { 'class' : 'value' } )[0].text.strip()
	else:
		return ''


# Returns 3-tuple of strings, one for supertypes, one for types, and one for subtypes.
def getTypes( soup , doubleSided = False, desiredSide = 'a' ):
	typetag = ''
	if doubleSided:
		if desiredSide == 'a':
			typetag = soup.find( 'div', { 'id' : 'ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_ctl07_typeRow', 'class' : 'row' } )
		elif desiredSide == 'b':
			typetag = soup.find( 'div', { 'id' : 'ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_ctl08_typeRow', 'class' : 'row' } )
	else:
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
				print 'Unknown type:', t
		supertypes = supertypes.strip()
		types = types.strip()
		if len( typelist ) > 1:
			subtypes = typelist[1].strip()

	return ( supertypes, types, subtypes )


def getRuleText( soup , doubleSided = False, desiredSide = 'a' ):
	texttag = ''
	if doubleSided:
		if desiredSide == 'a':
			texttag = soup.find( 'div', { 'id' : 'ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_ctl07_textRow', 'class' : 'row' } )
		elif desiredSide == 'b':
			texttag = soup.find( 'div', { 'id' : 'ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_ctl08_textRow', 'class' : 'row' } )
	else:
		texttag = soup.find( 'div', { 'id' : 'ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_textRow', 'class' : 'row' } )

	cardlines = []
	if texttag:
		rules = texttag.findChildren( 'div', { 'class' : 'value' } )[0].findChildren( 'div', { 'class' : 'cardtextbox' } )
		for r in rules:
			rulestring = unicode( r )
			symbols = re.findall( '<img.*?\&amp\;name=([\da-zA-Z]+)\&amp\;.*?\/>', rulestring )
			if symbols:
				for i in range( len( symbols ) ):
					if 'tap' in symbols[i]:
						symbols[i] = '{T}'
					elif 'snow' in symbols[i]:
						symbols[i] = '{S}'
					elif 'P' in symbols[i]:
						symbols[i] = '{' + symbols[i] + '}'
					else:
						symbols[i] = '{' + '/'.join( list( symbols[i] ) ) + '}'

				for s in symbols:
					rulestring = re.sub( '<img.*?/>', s, rulestring, 1 )

			rulestring = re.sub( '<.?div.*?>', '', rulestring )
			rulestring = re.sub( '<.?i>', '', rulestring )
			cardlines.append( rulestring )
	
	return '<br>'.join( filter( None, cardlines ) )

# Returns power, toughness as tuple.
def getPowerToughness( soup , doubleSided = False, desiredSide = 'a' ):
	pttag = ''
	if doubleSided:
		if desiredSide == 'a':
			pttag = soup.find( 'div', { 'id' : 'ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_ctl07_ptRow', 'class' : 'row' } )
		elif desiredSide == 'b':
			pttag = soup.find( 'div', { 'id' : 'ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_ctl08_ptRow', 'class' : 'row' } )
	else:
		pttag = soup.find( 'div', { 'id' : 'ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_ptRow', 'class' : 'row' } )

	if pttag:
		label = pttag.findChildren( 'div', { 'class' : 'label' } )[0].text.strip()
		if label == 'P/T:':
			pt = pttag.findChildren( 'div', { 'class' : 'value' } )[0].text.strip().split( '/' )
			return ( pt[0].strip(), pt[1].strip() )

	return ( '', '' )


def getLoyalty( soup , doubleSided = False, desiredSide = 'a' ):
	pttag = ''
	if doubleSided:
		if desiredSide == 'a':
			pttag = soup.find( 'div', { 'id' : 'ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_ctl07_ptRow', 'class' : 'row' } )
		elif desiredSide == 'b':
			pttag = soup.find( 'div', { 'id' : 'ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_ctl08_ptRow', 'class' : 'row' } )
	else:
		pttag = soup.find( 'div', { 'id' : 'ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_ptRow', 'class' : 'row' } )

	if pttag:
		label = pttag.findChildren( 'div', { 'class' : 'label' } )[0].text.strip()
		if label == 'Loyalty:':
			return pttag.findChildren( 'div', { 'class' : 'value' } )[0].text.strip()
	return ''

def getRarity( soup, doubleSided = False, desiredSide = 'a' ):
	raritytag = ''
	if doubleSided:
		if desiredSide == 'a':
			raritytag = soup.find( 'div', { 'id' : 'ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_ctl07_rarityRow', 'class' : 'row' } )
		elif desiredSide == 'b':
			raritytag = soup.find( 'div', { 'id' : 'ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_ctl08_rarityRow', 'class' : 'row' } )
	else:
		raritytag = soup.find( 'div', { 'id' : 'ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_rarityRow', 'class' : 'row' } )
	
	if raritytag:
		return raritytag.findChildren( 'div', { 'class' : 'value' } )[0].text.strip()
	else:
		return ''


def getArtist( soup, doubleSided = False, desiredSide = 'a' ):
	artisttag = ''
	if doubleSided:
		if desiredSide == 'a':
			artisttag = soup.find( 'div', { 'id' : 'ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_ctl07_artistRow', 'class' : 'row' } )
		elif desiredSide == 'b':
			artisttag = soup.find( 'div', { 'id' : 'ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_ctl08_artistRow', 'class' : 'row' } )
	else:
		artisttag = soup.find( 'div', { 'id' : 'ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_artistRow', 'class' : 'row' } )
	
	if artisttag:
		return artisttag.findChildren( 'div', { 'class' : 'value' } )[0].text.strip()
	else:
		return ''


def getSetName( soup, doubleSided = False, desiredSide = 'a' ):
	settag = ''
	if doubleSided:
		if desiredSide == 'a':
			settag = soup.find( 'div', { 'id' : 'ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_ctl07_setRow', 'class' : 'row' } )
		elif desiredSide == 'b':
			settag = soup.find( 'div', { 'id' : 'ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_ctl08_setRow', 'class' : 'row' } )
	else:
		settag = soup.find( 'div', { 'id' : 'ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_setRow', 'class' : 'row' } )
	
	if settag:
		return settag.findChildren( 'div', { 'class' : 'value' } )[0].text.strip()
	else:
		return ''


# Cards from early sets may not have a collector number, just so's ya know.
def getCollectorNumber( soup, doubleSided = False, desiredSide = 'a' ):
	cntag = ''
	if doubleSided:
		if desiredSide == 'a':
			cntag = soup.find( 'div', { 'id' : 'ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_ctl07_numberRow', 'class' : 'row' } )
		elif desiredSide == 'b':
			cntag = soup.find( 'div', { 'id' : 'ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_ctl08_numberRow', 'class' : 'row' } )
	else:
		cntag = soup.find( 'div', { 'id' : 'ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_numberRow', 'class' : 'row' } )
	
	if cntag:
		return cntag.findChildren( 'div', { 'class' : 'value' } )[0].text.strip()
	else:
		return ''


def getFlavorText( soup, doubleSided = False, desiredSide = 'a' ):
	flavortag = ''
	if doubleSided:
		if desiredSide == 'a':
			flavortag = soup.find( 'div', { 'id' : 'ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_ctl07_flavorRow', 'class' : 'row' } )
		elif desiredSide == 'b':
			flavortag = soup.find( 'div', { 'id' : 'ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_ctl08_flavorRow', 'class' : 'row' } )
	else:
		flavortag = soup.find( 'div', { 'id' : 'ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_flavorRow', 'class' : 'row' } )
	
	if flavortag:
		flavorlines = flavortag.findChildren( 'div', { 'class' : 'value' } )[0].findChildren( 'div', { 'class' : 'cardtextbox' } )
		p = re.compile( ur'\u2014', re.UNICODE )
		flavortext = [] 
		for flavor in flavorlines:
			flavortext.append( p.sub( '--', flavor.text ).strip() )
		return '<br>'.join( filter( None, flavortext ) )
	else:
		return ''


# Cards can be printed over many different sets, e.g. Naturalize. Make a list
# of these editions, where each list item is a tuple of the set name, collector
# number for that set, flavor text, and artist.
def getEditionsList( soup, doubleSided = False, desiredSide = 'a' ):
	alltag = ''
	if doubleSided:
		if desiredSide == 'a':
			alltag = soup.find( 'div', { 'id' : 'ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_ctl07_otherSetsRow', 'class' : 'row' } )
		elif desiredSide == 'b':
			alltag = soup.find( 'div', { 'id' : 'ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_ctl08_otherSetsRow', 'class' : 'row' } )
	else:
		alltag = soup.find( 'div', { 'id' : 'ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_otherSetsRow', 'class' : 'row' } )
	
	editions = []
	if alltag:
		setlinks = alltag.findChildren( 'div', { 'class' : 'value' } )[0].find_all( 'a' )
		for setlink in setlinks:
			m = re.search( '(\d+)$', setlink['href'] )
			if m:
				mid = m.groups()[0] # Multiverse ID
				othersoup = BeautifulSoup( urllib.urlopen( 'http://gatherer.wizards.com/Pages/Card/Details.aspx?multiverseid=' + m.groups()[0] ) )
				editions.append( ( mid,
								   getSetName( othersoup, doubleSided, desiredSide ),
								   getCollectorNumber( othersoup, doubleSided, desiredSide ),
								   getRarity( othersoup, doubleSided, desiredSide ),
								   getFlavorText( othersoup, doubleSided, desiredSide ),
								   getArtist( othersoup, doubleSided, desiredSide ) ) )
	else:
		mid = re.search( '(\d+)$', soup.find( 'form', { 'method' : 'post', 'id' : 'aspnetForm' } )['action'] ).groups()[0]
		editions.append( ( mid,
						   getSetName( soup, doubleSided, desiredSide ),
						   getCollectorNumber( soup, doubleSided, desiredSide ),
						   getRarity( soup, doubleSided, desiredSide ),
						   getFlavorText( soup, doubleSided, desiredSide ),
						   getArtist( soup, doubleSided, desiredSide ) ) )

	return editions


def isDoubleSided( soup ):
	nametag = soup.find( 'div', { 'id' : 'ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_ctl07_nameRow', 'class' : 'row' } )
	if nametag:
		return True
	else:
		return False


def scrapePage( multiverseId ):
	soup = BeautifulSoup( urllib.urlopen( 'http://gatherer.wizards.com/Pages/Card/Details.aspx?multiverseid=' + multiverseId ) )
	card = defaultdict( str )

	if not isDoubleSided( soup ):
		card['name'] = getName( soup )
		card['mana'] = getManaCost( soup )
		card['cmc'] = getConvertedManaCost( soup )
		card['supertype'], card['type'], card['subtype'] = getTypes( soup )
		card['rules'] = getRuleText( soup )
		card['power'], card['toughness'] = getPowerToughness( soup )
		card['loyalty'] = getLoyalty( soup )
		card['rarity'] = getRarity( soup )
		card['editions'] = getEditionsList( soup )
	else:
		# Figure out which side corresponds to this multiverseId
		subtitle = soup.find( 'span', { 'id' : 'ctl00_ctl00_ctl00_MainContent_SubContent_SubContentHeader_subtitleDisplay' } )
		desiredSide = 'a'
		if getName( soup, True, 'b' ) == subtitle.text.strip():
			desiredSide = 'b'

		card['name'] = getName( soup, True, desiredSide )
		card['mana'] = getManaCost( soup, True, desiredSide )
		card['cmc'] = getConvertedManaCost( soup, True, desiredSide )
		card['supertype'], card['type'], card['subtype'] = getTypes( soup, True, desiredSide )
		card['rules'] = getRuleText( soup, True, desiredSide )
		card['power'], card['toughness'] = getPowerToughness( soup, True, desiredSide )
		card['loyalty'] = getLoyalty( soup, True, desiredSide )
		card['rarity'] = getRarity( soup, True, desiredSide )
		card['editions'] = getEditionsList( soup, True, desiredSide )

	return card


def printCard( card ):
	print 'Name =', card['name']
	if card['mana']:
		print 'Cost =', card['mana']
	if card['cmc']:
		print 'CMC =', card['cmc']
	if card['supertype']:
		print 'Supertypes =', card['supertype']
	if card['type']:
		print 'Types =', card['type']
	if card['subtype']:
		print 'Subtypes =', card['subtype']
	if card['rules']:
		print 'Rules text =', card['rules']
	if card['power']:
		print 'Power =', card['power']
	if card['toughness']:
		print 'Toughness =', card['toughness']
	if card['loyalty']:
		print 'Loyalty =', card['loyalty']
	print 'Editions =', card['editions']


def saveMasterList():
	soup = BeautifulSoup( urllib.urlopen( 'http://gatherer.wizards.com/Pages/Search/Default.aspx?page=0&name=+[]' ) )
	lastpagelink = soup.find( 'div', { 'class' : 'pagingcontrols' } ).findChildren( 'a' )[-1]
	numPages = int( re.search( 'page=(.*?)\&', lastpagelink['href'] ).groups()[0] )

	cardlist = []
	for pageNum in range( 4, numPages + 1 ):
		print 'On page ', pageNum
		soup = BeautifulSoup( urllib.urlopen( 'http://gatherer.wizards.com/Pages/Search/Default.aspx?page={}&name=+[]'.format( str( pageNum ) ) ) )

		cardLinks = soup.find_all( 'a', id = lambda x: x and x.endswith('cardTitle') )
		for cardlink in cardLinks:
			multiverseId = re.search( 'multiverseid=(\d+)', cardlink['href'] ).groups()[0]
			c = scrapePage( multiverseId )
			print '=' * 80
			printCard( c )
#			raw_input( "Next..." )


saveMasterList()

#ids = [ '218043', '159408', '153471', '73935', '201563', '366303', '121268', '266299', '262675', '262698', '292753' ]
#for i in ids:
#	print '=' * 80
#	c = scrapePage( i )
#	printCard( c )

