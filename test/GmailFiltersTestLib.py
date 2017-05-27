import os
import sys
import unittest

# Make sure that the parent directory is in path
testDir = os.path.dirname( __file__ )
baseDir = os.path.realpath( os.path.join( testDir, '..' ) )
sys.path = [ baseDir ] + sys.path

from GmailFilters import FilterElement, parse_filter_element

# for debugging
def pm( func ):
   def _wrapper( *args, **kwargs ):
      try:
         func( *args, **kwargs )
      except:
         import pdb
         import traceback
         traceback.print_exc()
         pdb.post_mortem()
         raise
   return _wrapper

# Short aliases
def grp( *subElems, **kwargs ):
   return FilterElement( subElems=list( subElems ), **kwargs )

def grp2( *subElems, **kwargs ):
   return grp( grp( *subElems, **kwargs ) )

def prs( string ):
   return parse_filter_element( string )

def prs1( string ):
   return prs( string ).subElems[ 0 ]

class ParserTestBase( unittest.TestCase ):
   def parse_str( self, string ):
      return parse_filter_element( string )
