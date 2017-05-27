from __future__ import print_function
import sys

class GmailFilter( object ):
   pass

# delimiters
PARENS = '()'
BRACES = '{}'

DELIM_PAIRS = [ PARENS, BRACES ]
OPEN_DELIMS = '({'
CLOSE_DELIMS = ')}'

class ParseError( Exception ):
   pass

class FilterElement( object ):
   def __init__( self, filterStr=None, subElems=None, delims=None,
                 preWs='', postWs='' ):
      self.filterStr = filterStr
      self.subElems = subElems
      self.delims = delims
      self.preWs = preWs
      self.postWs = postWs
      self._check_consistency()

   def __eq__( self, other ):
      return type( self ) is type( other ) and \
            self.filterStr == other.filterStr and \
            self.subElems == other.subElems and \
            self.delims == other.delims and \
            self.preWs == other.preWs and \
            self.postWs == other.postWs

   def _check_consistency( self ):
      assert ( self.filterStr is None and self.subElems ) or \
             ( self.filterStr is not None and self.subElems is None )

   def has_sub_elems( self ):
      self._check_consistency()
      return self.subElems is not None

   def _maybe_wrap_in_delims( self, string ):
      if self.delims is not None:
         return self.delims[ 0 ] + string + self.delims[ 1 ]

      return string

   def _maybe_wrap_in_delims_and_pad( self, string ):
      string = self._maybe_wrap_in_delims( string )
      return self.preWs + string + self.postWs

   def full_filter_str( self ):
      self._check_consistency()
      if self.has_sub_elems():
         return self._maybe_wrap_in_delims_and_pad(
               ''.join( sg.full_filter_str() for sg in self.subElems ) )

      return self._maybe_wrap_in_delims_and_pad( self.filterStr )

   @staticmethod
   def full_filter_list_str( filterElementList ):
      return ''.join( fe.full_filter_str() for fe in filterElementList )

   def __str__( self ):
      return self.full_filter_str()

   def repr( self, **kwargs ):
      return '\n'.join( self._repr_lines( **kwargs ) )

   def _repr_lines( self, hexid=False, indent=0, singleLine=False ):
      def indented( string, extra=0 ):
         if singleLine:
            return string
         return ( ' ' * ( indent + extra ) ) + string

      reprLines = []
      reprStr = indented( 'FilterElement' )
      if hexid:
         reprStr += '<%s>' % hex( id( self ) )

      reprStr += '('

      def append_attr( attrName, attr, addComma=True ):
         nonlocal reprStr
         comma = ', ' if addComma else ''
         attrStr = "%s=%s%s" % ( attrName, attr, comma )
         reprStr += attrStr

      def maybe_append_simple( attrName, attr ):
         if attr != "''" and attr != 'None':
            append_attr( attrName, attr )

      maybe_append_simple( 'filterStr', repr( self.filterStr ) )
      maybe_append_simple( 'delims', repr( self.delims ) )
      maybe_append_simple( 'preWs', repr( self.preWs ) )
      maybe_append_simple( 'postWs', repr( self.postWs ) )

      if self.subElems is not None:
         append_attr( 'subElems', '[', addComma=False )
         allSeLines = []
         for se in self.subElems:
            # pylint: disable=protected-access
            seLines = se._repr_lines( hexid=hexid, indent=indent + 2,
                                      singleLine=singleLine )
            seLines[ -1 ] += ','
            allSeLines.extend( seLines )

         if not singleLine:
            reprLines.append( reprStr )
            reprLines.extend( allSeLines )
            reprStr = indented( ']', extra=2 )
         else:
            reprStr += ''.join( allSeLines ) + ']'

      reprStr += ')'
      reprLines.append( reprStr )
      return reprLines

   def __repr__( self ):
      return self.repr( singleLine=True )

PRE_TEXT_MODE = 'pre'
TEXT_MODE = 'text'
POST_TEXT_MODE = 'post'
QUOTED_TEXT_MODE = 'quoted'

class ElementParser( object ):
   def __init__( self, filterStr, startIdx=0, lastIdx=None ):
      self.filterStr = filterStr
      if lastIdx is None:
         lastIdx = len( filterStr ) - 1
      self.startIdx = startIdx
      self.currIdx = startIdx
      self.lastIdx = lastIdx

   def last_group_idx( self, groupStart ):
      delimStack = []
      i = groupStart
      assert self.filterStr[ i ] in OPEN_DELIMS
      while True:
         c = self.filterStr[ i ]
         if c in OPEN_DELIMS:
            di = OPEN_DELIMS.index( c )
            delimStack.append( c )
         elif c in CLOSE_DELIMS:
            di = CLOSE_DELIMS.index( c )
            if not delimStack or delimStack[ -1 ] != OPEN_DELIMS[ di ]:
               raise ParseError( "Mismatched closing delim at index " + i )
            else:
               delimStack.pop()

         if not delimStack:
            break
         i += 1

      return i

   def parse_delimited_group( self, startIdx ):
      '''Return ( group, lastIdx )'''
      lastDelimIdx = self.last_group_idx( startIdx )
      assert lastDelimIdx

      subElmParser = ElementParser( self.filterStr, startIdx + 1, lastDelimIdx - 1 )
      groupElem = subElmParser.parse()
      groupElem.delims = '()' if self.filterStr[ startIdx ] == '(' else '{}'

      return groupElem, lastDelimIdx

   def parse_next( self ):
      # pylint: disable=too-many-branches,too-many-statements
      mode = PRE_TEXT_MODE
      delims = None
      substr = None
      groupElem = None
      preWs = ''
      postWs = ''
      isFirstParse = self.startIdx == self.currIdx
      i = self.currIdx
      while i <= self.lastIdx:
         if mode == PRE_TEXT_MODE:
            if self.filterStr[ i ] == ' ':
               preWs += ' '
            elif self.filterStr[ i ] in OPEN_DELIMS:
               groupElem, i = self.parse_delimited_group( i )
               mode = POST_TEXT_MODE
            elif self.filterStr[ i ] in CLOSE_DELIMS:
               assert 0, "Found unmatched close delim while parsing: idx %d" % i
            elif self.filterStr[ i ] == '"':
               mode = QUOTED_TEXT_MODE
               delims = '""'
               substr = ''
            else:
               mode = TEXT_MODE
               substr = self.filterStr[ i ]

         elif mode == TEXT_MODE:
            if self.filterStr[ i ] == ' ':
               mode = POST_TEXT_MODE
               postWs += ' '
            elif self.filterStr[ i ] in OPEN_DELIMS:
               break
            elif self.filterStr[ i ] in CLOSE_DELIMS:
               assert 0, "Found unmatched close delim while parsing: idx %d" % i
            elif self.filterStr[ i ] == '"':
               # This quoted element will be next
               break
            else:
               substr += self.filterStr[ i ]

         elif mode == POST_TEXT_MODE:
            if self.filterStr[ i ] == ' ':
               postWs += ' '
            else:
               break

         elif mode == QUOTED_TEXT_MODE:
            if self.filterStr[ i ] == '"':
               i += 1
               break
            else:
               substr += self.filterStr[ i ]
         else:
            assert 0, mode
         i += 1

      self.currIdx = i
      if substr is None and groupElem is None:
         if isFirstParse:
            substr = ''
            if self.currIdx == self.startIdx:
               self.currIdx = self.startIdx + 1
         else:
            assert not preWs and not postWs
            return None

      if groupElem is not None:
         elm = groupElem
         elm.preWs = preWs
         elm.postWs = postWs
      else:
         elm = FilterElement( substr,
                              delims=delims,
                              preWs=preWs,
                              postWs=postWs )
      return elm

   def parse( self ):
      delimsError = self.check_delims()
      if delimsError is not None:
         raise ParseError( delimsError )

      filterElements = []
      done = False
      while not done:
         nextElem = self.parse_next()
         if nextElem is None:
            done = True
         else:
            filterElements.append( nextElem )

      return FilterElement( subElems=filterElements )

   def parse_error( self, index ):
      return self.filterStr + '\n' + ( ( ' ' * index ) + '^' )

   def check_delims( self ):
      delimStack = []
      for i, c in enumerate( self.filterStr ):
         if c in OPEN_DELIMS:
            di = OPEN_DELIMS.index( c )
            delimStack.append( c )
         elif c in CLOSE_DELIMS:
            di = CLOSE_DELIMS.index( c )
            if not delimStack or delimStack[ -1 ] != OPEN_DELIMS[ di ]:
               return "Mismatched closing delim:\n" + self.parse_error( i )
            else:
               delimStack.pop()
      if delimStack:
         return "Unmatched delim:\n" + \
                self.parse_error( len( self.filterStr ) - 1 )

      if self.filterStr.count( '"' ) % 2:
         return "Unmatched quote"

      return None

def parse_filter_element( filterStr ):
   p = ElementParser( filterStr )
   return p.parse()
