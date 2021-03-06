#!/usr/bin/env python

from bs4 import BeautifulSoup
import urllib
import re
import os
from collections import defaultdict
import codecs
from optparse import OptionParser
import Queue
import random
import sys
import threading
import time
 
Basis = 'ctl00_ctl00_ctl00_MainContent_SubContent_SubContent'

def getName( soup, doubleSided = False, desiredSide = 'a' ):
	nametag = ''
	if doubleSided:
		if desiredSide == 'a':
			nametag = soup.find( 'div', { 'id' : Basis + '_ctl07_nameRow', 'class' : 'row' } )
		elif desiredSide == 'b':
			nametag = soup.find( 'div', { 'id' : Basis + '_ctl08_nameRow', 'class' : 'row' } )
	else:
		nametag = soup.find( 'div', { 'id' : Basis + '_nameRow', 'class' : 'row' } )

	if nametag:
		return nametag.findChildren( 'div', { 'class' : 'value' } )[0].text.strip()
	else:
		return ''


def getManaCost( soup, doubleSided = False, desiredSide = 'a' ):
	manatag = ''
	if doubleSided:
		if desiredSide == 'a':
			manatag = soup.find( 'div', { 'id' : Basis + '_ctl07_manaRow', 'class' : 'row' } )
		elif desiredSide == 'b':
			manatag = soup.find( 'div', { 'id' : Basis + '_ctl08_manaRow', 'class' : 'row' } )
	else:
		manatag = soup.find( 'div', { 'id' : Basis + '_manaRow', 'class' : 'row' } )

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
					manastring += ( '{' + '/'.join( filter( None, re.split( '([A-Z]|\d+)', m.groups()[0] ) ) ) + '}' )
	return manastring


def getConvertedManaCost( soup, doubleSided = False, desiredSide = 'a' ):
	cmctag = ''
	if doubleSided:
		if desiredSide == 'a':
			cmctag = soup.find( 'div', { 'id' : Basis + '_ctl07_cmcRow', 'class' : 'row' } )
		elif desiredSide == 'b':
			cmctag = soup.find( 'div', { 'id' : Basis + '_ctl08_cmcRow', 'class' : 'row' } )
	else:
		cmctag = soup.find( 'div', { 'id' : Basis + '_cmcRow', 'class' : 'row' } )

	if cmctag:
		return cmctag.findChildren( 'div', { 'class' : 'value' } )[0].text.strip()
	else:
		return ''


# Returns 3-tuple of strings, one for supertypes, one for types, and one for subtypes.
def getTypes( soup , doubleSided = False, desiredSide = 'a' ):
	typetag = ''
	if doubleSided:
		if desiredSide == 'a':
			typetag = soup.find( 'div', { 'id' : Basis + '_ctl07_typeRow', 'class' : 'row' } )
		elif desiredSide == 'b':
			typetag = soup.find( 'div', { 'id' : Basis + '_ctl08_typeRow', 'class' : 'row' } )
	else:
		typetag = soup.find( 'div', { 'id' : Basis + '_typeRow', 'class' : 'row' } )

	supertypes = []
	types = []
	subtypes = ''
	if typetag:
		typestring = typetag.findChildren( 'div', { 'class' : 'value' } )[0].text.strip()
		typelist = re.compile( ur'\u2014', re.UNICODE ).split( typestring )
		for t in typelist[0].split( ' ' ):
			if t in ['Basic', 'Legendary', 'Snow', 'World']:
				supertypes.append( t )
			elif t in ['Artifact', 'Creature', 'Enchantment', 'Land', 'Planeswalker', 'Tribal', 'Instant', 'Sorcery']:
				types.append( t )
			elif t == 'Summon':
				types.append( 'Creature' )
			elif t == 'Interrupt':
				types.append( 'Instant' )
			elif t == 'Enchant':
				types.append( 'Enchantment' )
			elif t and t != '(none)': # Tokens are listed with (none) type
				sys.stderr.write( 'Weird type:' + t + '\n' )
				types.append( t )
		if len( typelist ) > 1:
			subtypes = typelist[1].strip()

	return ( ' '.join( supertypes ), ' '.join( types ), subtypes )


def getRuleText( soup , doubleSided = False, desiredSide = 'a' ):
	texttag = ''
	if doubleSided:
		if desiredSide == 'a':
			texttag = soup.find( 'div', { 'id' : Basis + '_ctl07_textRow', 'class' : 'row' } )
		elif desiredSide == 'b':
			texttag = soup.find( 'div', { 'id' : Basis + '_ctl08_textRow', 'class' : 'row' } )
	else:
		texttag = soup.find( 'div', { 'id' : Basis + '_textRow', 'class' : 'row' } )

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
						symbols[i] = '{' + '/'.join( filter( None, re.split( '([A-Z]|\d+)', symbols[i] ) ) ) + '}'

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
			pttag = soup.find( 'div', { 'id' : Basis + '_ctl07_ptRow', 'class' : 'row' } )
		elif desiredSide == 'b':
			pttag = soup.find( 'div', { 'id' : Basis + '_ctl08_ptRow', 'class' : 'row' } )
	else:
		pttag = soup.find( 'div', { 'id' : Basis + '_ptRow', 'class' : 'row' } )

	if pttag:
		label = pttag.findChildren( 'div', { 'class' : 'label' } )[0].text.strip()
		if label == 'P/T:':
			m = re.search( '^(.*) \/ (.*)$', pttag.findChildren( 'div', { 'class' : 'value' } )[0].text.strip() )
			if m:
				return ( m.groups()[0], m.groups()[1] )

	return ( '', '' )


def getLoyalty( soup , doubleSided = False, desiredSide = 'a' ):
	pttag = ''
	if doubleSided:
		if desiredSide == 'a':
			pttag = soup.find( 'div', { 'id' : Basis + '_ctl07_ptRow', 'class' : 'row' } )
		elif desiredSide == 'b':
			pttag = soup.find( 'div', { 'id' : Basis + '_ctl08_ptRow', 'class' : 'row' } )
	else:
		pttag = soup.find( 'div', { 'id' : Basis + '_ptRow', 'class' : 'row' } )

	if pttag:
		label = pttag.findChildren( 'div', { 'class' : 'label' } )[0].text.strip()
		if label == 'Loyalty:':
			return pttag.findChildren( 'div', { 'class' : 'value' } )[0].text.strip()
	return ''

def getRarity( soup, doubleSided = False, desiredSide = 'a' ):
	raritytag = ''
	if doubleSided:
		if desiredSide == 'a':
			raritytag = soup.find( 'div', { 'id' : Basis + '_ctl07_rarityRow', 'class' : 'row' } )
		elif desiredSide == 'b':
			raritytag = soup.find( 'div', { 'id' : Basis + '_ctl08_rarityRow', 'class' : 'row' } )
	else:
		raritytag = soup.find( 'div', { 'id' : Basis + '_rarityRow', 'class' : 'row' } )
	
	if raritytag:
		return raritytag.findChildren( 'div', { 'class' : 'value' } )[0].text.strip()
	else:
		return ''


def getArtist( soup, doubleSided = False, desiredSide = 'a' ):
	artisttag = ''
	if doubleSided:
		if desiredSide == 'a':
			artisttag = soup.find( 'div', { 'id' : Basis + '_ctl07_artistRow', 'class' : 'row' } )
		elif desiredSide == 'b':
			artisttag = soup.find( 'div', { 'id' : Basis + '_ctl08_artistRow', 'class' : 'row' } )
	else:
		artisttag = soup.find( 'div', { 'id' : Basis + '_artistRow', 'class' : 'row' } )
	
	if artisttag:
		return artisttag.findChildren( 'div', { 'class' : 'value' } )[0].text.strip()
	else:
		return ''


def getSetName( soup, doubleSided = False, desiredSide = 'a' ):
	settag = ''
	if doubleSided:
		if desiredSide == 'a':
			settag = soup.find( 'div', { 'id' : Basis + '_ctl07_setRow', 'class' : 'row' } )
		elif desiredSide == 'b':
			settag = soup.find( 'div', { 'id' : Basis + '_ctl08_setRow', 'class' : 'row' } )
	else:
		settag = soup.find( 'div', { 'id' : Basis + '_setRow', 'class' : 'row' } )
	
	if settag:
		return settag.findChildren( 'div', { 'class' : 'value' } )[0].text.strip()
	else:
		return ''


# Cards from early sets may not have a collector number, just so's ya know.
def getCollectorNumber( soup, doubleSided = False, desiredSide = 'a' ):
	cntag = ''
	if doubleSided:
		if desiredSide == 'a':
			cntag = soup.find( 'div', { 'id' : Basis + '_ctl07_numberRow', 'class' : 'row' } )
		elif desiredSide == 'b':
			cntag = soup.find( 'div', { 'id' : Basis + '_ctl08_numberRow', 'class' : 'row' } )
	else:
		cntag = soup.find( 'div', { 'id' : Basis + '_numberRow', 'class' : 'row' } )
	
	if cntag:
		return cntag.findChildren( 'div', { 'class' : 'value' } )[0].text.strip()
	else:
		return ''


def getFlavorText( soup, doubleSided = False, desiredSide = 'a' ):
	flavortag = ''
	if doubleSided:
		if desiredSide == 'a':
			flavortag = soup.find( 'div', { 'id' : Basis + '_ctl07_flavorRow', 'class' : 'row' } )
		elif desiredSide == 'b':
			flavortag = soup.find( 'div', { 'id' : Basis + '_ctl08_flavorRow', 'class' : 'row' } )
	else:
		flavortag = soup.find( 'div', { 'id' : Basis + '_flavorRow', 'class' : 'row' } )
	
	if flavortag:
		flavorlines = flavortag.findChildren( 'div', { 'class' : 'value' } )[0].findChildren( 'div', { 'class' : 'cardtextbox' } )
		flavortext = [] 
		for flavor in flavorlines:
			flavortext.append( flavor.text.strip() ) 
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
			alltag = soup.find( 'div', { 'id' : Basis + '_ctl07_otherSetsRow', 'class' : 'row' } )
		elif desiredSide == 'b':
			alltag = soup.find( 'div', { 'id' : Basis + '_ctl08_otherSetsRow', 'class' : 'row' } )
	else:
		alltag = soup.find( 'div', { 'id' : Basis + '_otherSetsRow', 'class' : 'row' } )
	
	editions = []
	if alltag:
		setlinks = alltag.findChildren( 'div', { 'class' : 'value' } )[0].find_all( 'a' )
		for setlink in setlinks:
			m = re.search( '(\d+)$', setlink['href'] )
			if m:
				mid = m.groups()[0] # Multiverse ID
				othersoup = BeautifulSoup( urllib.urlopen( 'http://gatherer.wizards.com/Pages/Card/Details.aspx?multiverseid=' + mid ) )
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
	nametag = soup.find( 'div', { 'id' : Basis + '_ctl07_nameRow', 'class' : 'row' } )
	if nametag:
		return True
	else:
		return False


def scrapePage( soup ):
	card = defaultdict( str )

	card['mid'] = re.search( '(\d+)$', soup.find( 'form', { 'method' : 'post', 'id' : 'aspnetForm' } )['action'] ).groups()[0]

	if not isDoubleSided( soup ):
		card['name'] = getName( soup )
		card['mana'] = getManaCost( soup )
		card['cmc'] = getConvertedManaCost( soup )
		card['supertype'], card['type'], card['subtype'] = getTypes( soup )
		card['rules'] = getRuleText( soup )
		card['power'], card['toughness'] = getPowerToughness( soup )
		card['loyalty'] = getLoyalty( soup )
		card['set'] = getSetName( soup )
		card['number'] = getCollectorNumber( soup )
		card['rarity'] = getRarity( soup )
		card['flavor'] = getFlavorText( soup )
		card['artist'] = getArtist( soup )
	else:
		# Figure out which side corresponds to this multiverseId
		subtitle = soup.find( 'span', { 'id' : Basis + 'Header_subtitleDisplay' } )
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
		card['set'] = getSetName( soup, True, desiredSide )
		card['number'] = getCollectorNumber( soup, True, desiredSide )
		card['rarity'] = getRarity( soup, True, desiredSide )
		card['flavor'] = getFlavorText( soup, True, desiredSide )
		card['artist'] = getArtist( soup, True, desiredSide )

	return card


def printCard( card, filehandle = None ):
	attributes = [ 'name', 'mid', 'mana', 'cmc', 'supertype', 'type', 'subtype',
					'rules', 'power', 'toughness', 'loyalty', 'set', 'number',
					'rarity', 'flavor', 'artist' ]
	if filehandle:
		filehandle.write( '<card>\n' )
		for attr in attributes:
			if card[attr]:
				filehandle.write( '\t<' + attr + '>' + card[attr] + '</' + attr + '>\n' )
		filehandle.write( '</card>\n' )
	else:
		print '<card>'
		for attr in attributes:
			if card[attr]:
				print '\t<' + attr + '>' + card[attr] + '</' + attr + '>'
		print '</card>'


midQueue = Queue.Queue()
soupQueue = Queue.Queue()
cards = []
cardsMutex = threading.Lock()
 
def producer( idNum ):
	while not midQueue.empty():
		mid = midQueue.get( block = False )
		while True:
			try:
				soup = BeautifulSoup( urllib.urlopen( 'http://gatherer.wizards.com/Pages/Card/Details.aspx?multiverseid=' + mid ) )
				break
			except IOError:
				print 'Error getting card.'
				time.sleep( 1 )
				pass
		soupQueue.put( soup )

def consumer( idNum, totalCards, setName ):
	while len( cards ) < int( totalCards ):
		try:
			soup = soupQueue.get( block = False )
		except Queue.Empty:
			pass
		else:
			c = scrapePage( soup )
			with cardsMutex:
				cards.append( c )
				percent = str( round( len( cards ) * 1.0 / totalCards * 100, 0 ) )
				sys.stdout.write( '\r' + setName + ' :: ' + percent + '%' )
				sys.stdout.flush()
			soupQueue.task_done()


def saveSet( setName ):
	soup = BeautifulSoup( urllib.urlopen( 'http://gatherer.wizards.com/Pages/Search/Default.aspx?output=checklist&action=advanced&set=|[%22' + '+'.join( setName.split() ) + '%22]' ) )
	cardLinks = soup.find_all( 'a', { 'class' : 'nameLink' } )

	for link in cardLinks:
		m = re.search( '(\d+)$', link['href'] )
		if m:
			mid = m.group( 0 )
			midQueue.put( mid )

	numProducers = 10
	numConsumers = 5

	joinable = []
	for i in range( numProducers ):
		t = threading.Thread( target = producer, args = ( i, ) )
		joinable.append( t )
		t.start()

	for i in range( numConsumers ):
		t = threading.Thread( target = consumer, args = ( i, len( cardLinks ), setName ) )
		joinable.append( t )
		t.start()

	# Wait for all threads to finish.
	for t in joinable: t.join()
	soupQueue.join()

	print ' :: (wrote', len( cards ), 'cards)'
	xmlfile = codecs.open( 'sets/%s.xml' % '_'.join( setName.split() ), 'w', 'utf-8' )

	# Sort cards using collector numbers as keys; use the name if there is no number.
	def gimmekey( x ):
		if 'number' in x:
			if 'a' in x['number'] or 'b' in x['number']:
				return int( x['number'][:-1] )
			else:
				return int( x['number'] )
		else:
			return x['name']

	cards.sort( key = lambda x: gimmekey( x ) )
	for c in cards:
		printCard( c, xmlfile )
	xmlfile.close()
 
if __name__ == '__main__':
	usage = 'usage: %prog [-a|-s <set name>]\nScrape card information from gatherer.wizards.com into XML files.'
	parser = OptionParser( usage = usage )
	parser.add_option( '-a', '--all',
						action = 'store_true', dest = 'downloadAll',
						help = 'Scrape information for all Magic: The Gathering sets.' )
	parser.add_option( '-s', '--set',
						metavar = 'SETNAME', help = 'Download a specific set. See allsets file for recognized sets.' )

	( options, args ) = parser.parse_args()

	allsets = open( 'allsets' )
	setNames = []
	for s in allsets:
		s = s.strip()
		if s and s[0] != '#':
			setNames.append( s )

	if not os.path.exists( 'sets' ):
		os.makedirs( 'sets' )

	if options.set:
		if options.set in setNames:
			saveSet( options.set )
		else:
			print 'Not a recognized set name.'
			parser.print_help()
	else:
		for s in setNames:
			cards = []
			saveSet( s )

