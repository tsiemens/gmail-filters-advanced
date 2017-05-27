#!/usr/bin/env python3

import unittest

from GmailFiltersTestLib import pm, grp, grp2, prs, prs1, ParserTestBase
from GmailFilters import ElementParser, ParseError
from GmailFilters import FilterElement as Fe

class ParsingTest( ParserTestBase ):
   def testCheckDelims( self ):
      def check( string ):
         return ElementParser( string ).check_delims() is None

      self.assertTrue( check( "()" ) )
      self.assertTrue( check( "{}" ) )
      self.assertTrue( check( "(xx)" ) )
      self.assertTrue( check( "zz (xx) yy" ) )
      self.assertTrue( check( "(x ())" ) )
      self.assertTrue( check( "(x ({({x})} () ))(){(y)}" ) )

      self.assertFalse( check( "(" ) )
      self.assertFalse( check( "{" ) )
      self.assertFalse( check( ")" ) )
      self.assertFalse( check( "}" ) )
      self.assertFalse( check( "((})" ) )
      self.assertFalse( check( "(()" ) )
      self.assertFalse( check( "())" ) )
      self.assertFalse( check( "xx{xx(xx)xxx)xx" ) )
      self.assertFalse( check( '"' ) )
      self.assertFalse( check( '"xxx" xx "x ' ) )

   @pm
   def testParse( self ):
      def checkParse( filterStr, expectedElems ):
         fes = self.parse_str( filterStr )
         self.assertEqual( fes, expectedElems )
         self.assertEqual( str( fes ), filterStr )

      # Empty
      checkParse( '', grp( Fe( '' ) ) )
      checkParse( ' ', grp( Fe( '', preWs=' ' ) ) )
      checkParse( '  ', grp( Fe( '', preWs='  ' ) ) )

      # Single
      checkParse( 'bla', grp( Fe( 'bla' ) ) )
      checkParse( ' bla', grp( Fe( 'bla', preWs=' ' ) ) )
      checkParse( '  bla', grp( Fe( 'bla', preWs='  ' ) ) )
      checkParse( 'foo:bar', grp( Fe( 'foo:bar' ) ) )

      # Multiple
      checkParse( 'foo bar', grp( prs1( 'foo ' ), prs1( 'bar' ) ) )
      checkParse( ' foo  bar ', grp( prs1( ' foo  ' ), prs1( 'bar ' ) ) )

      # Group
      checkParse( '()', grp2( prs1( '' ), delims='()' ) )
      checkParse( '( )', grp2( prs1( ' ' ), delims='()' ) )
      checkParse( '{x}', grp2( prs1( 'x' ), delims='{}' ) )
      checkParse( ' {x} ', grp2( prs1( 'x' ), delims='{}', preWs=' ', postWs=' ' ) )
      checkParse( '{ x y}', grp2( *prs( ' x y' ).subElems, delims='{}' ) )

      # Multiple groups
      checkParse( '{x}(y)', grp( prs1( '{x}' ), prs1( '(y)' ) ) )
      checkParse( ' {x} (y) ', grp( prs1( ' {x} ' ), prs1( '(y) ' ) ) )
      checkParse( ' x (y) ', grp( prs1( ' x ' ), prs1( '(y) ' ) ) )
      checkParse( ' (y) x ', grp( prs1( ' (y) ' ), prs1( 'x ' ) ) )
      checkParse( ' x:(y) ', grp( prs1( ' x:' ), prs1( '(y) ' ) ) )
      checkParse( '(y)x', grp( prs1( '(y)' ), prs1( 'x' ) ) )

      # Nested groups
      checkParse( '{()}', grp2( prs1( '()' ), delims='{}' ) )
      checkParse( '{(x)}', grp2( prs1( '(x)' ), delims='{}' ) )

      # Quotes
      checkParse( '""', grp( Fe( '', delims='""' ) ) )
      checkParse( '"(blar)"', grp( Fe( '(blar)', delims='""' ) ) )
      checkParse( '("(blar)")', grp2( prs1( '"(blar)"' ), delims='()' ) )

      # Life-like
      subjectFooBarElemGrp = prs( 'subject:("Fo bar")' )
      self.assertEqual( subjectFooBarElemGrp, grp(
         Fe( 'subject:' ),
         grp( Fe( 'Fo bar', delims='""' ), delims='()' ),
         ) )
      metaFooElem = prs1( '{(M3TA label=foo) from:bla@gmail.com} ' )
      self.assertEqual( metaFooElem, grp(
         prs1( '(M3TA label=foo) ' ),
         Fe( 'from:bla@gmail.com' ),
         delims='{}',
         postWs=' '
         )
      )

      checkParse(
            '({(M3TA label=foo) from:bla@gmail.com} subject:("Fo bar")) '
            'OR Foo',
            grp( grp( metaFooElem, *subjectFooBarElemGrp.subElems,
                      delims='()', postWs=' ' ),
                 prs1( 'OR ' ),
                 prs1( 'Foo' )
               )
            )

   def testErrors( self ):
      self.assertRaises( ParseError, self.parse_str, '(' )
      self.assertRaises( ParseError, self.parse_str, ')' )
      self.assertRaises( ParseError, self.parse_str, '({)' )
      # While technically valid, this is not supported right now
      self.assertRaises( ParseError, self.parse_str, '("xx)")' )

if __name__ == '__main__':
   unittest.main()
