#!/usr/bin/env python3

import unittest

from GmailFiltersTestLib import pm, grp, grp2, prs, prs1, ParserTestBase
from GmailFilters.Template import get_meta_group_key, \
                                  find_primary_template_group, \
                                  sub_meta_groups, \
                                  update_all_meta_groups, \
                                  find_all_meta_group_keys, \
                                  TemplateError

class ParsingTest( ParserTestBase ):
   @pm
   def testMetaKey( self ):
      def check( filterStr, key, raises=False ):
         elem = prs1( filterStr )
         if raises:
            self.assertRaises( TemplateError, get_meta_group_key, elem )
         else:
            self.assertEqual( get_meta_group_key( elem ), key )

      check( '(M3TA xxx)', ( 'xxx', ) )
      check( '(xxx M3TA bla)', ( 'bla', 'xxx' ) )
      check( '(bla M3TA xxx)', ( 'bla', 'xxx' ) )
      check( '(xxx M3TA (bla))', ( '(bla)', 'xxx' ) )
      check( '(M3TA)', None, raises=True )
      check( 'M3TA xxx', None )
      check( 'M3TA', None )
      check( '"M3TA xxx"', ( 'xxx', ) )
      check( '"M3TA xxx bla"', ( 'bla', 'xxx' ) )
      check( '"xxx M3TA"', ( 'xxx', ) )
      check( '"M3TA"', None, raises=True )

   @pm
   def testFindPrimary( self ):
      def check( filterStr, primaryStr ):
         filterGroup = prs( filterStr )
         if primaryStr is not None:
            expectedGrp = prs1( primaryStr )
         else:
            expectedGrp = None

         self.assertEqual( find_primary_template_group( filterGroup ),
                           expectedGrp )

      def checkRaises( filterStr ):
         filterGroup = prs( filterStr )
         self.assertRaises( TemplateError,
                            find_primary_template_group, filterGroup )

      check( '{}', None )
      check( '{(M3TA bla)}', '{(M3TA bla)}' )
      check( '{xx (M3TA bla)}', '{xx (M3TA bla)}' )
      check( '{(M3TA bla) yy}', '{(M3TA bla) yy}' )
      check( '({(M3TA bla) yy})', '{(M3TA bla) yy}' )
      checkRaises( '{(M3TA bla) yy (M3TA foo)}' )

   @pm
   def testReplace( self ):
      primary = '{(M3TA foo) (thing) thing2}'
      primaryGrp = find_primary_template_group( prs( primary ) )

      def check( filterStr, newFilterStr ):
         filterGroup = prs( filterStr )
         sub_meta_groups( filterGroup, primaryGrp )
         self.assertEqual( str( filterGroup ), newFilterStr )

      check( 'something {( fo) x}', 'something {( fo) x}' )
      check( 'something {(M3TA fo) x}', 'something {(M3TA fo) x}' )
      check( 'something {(M3TA foo) x}', 'something ' + primary )
      check( 'something {(M3TA foo) x} ({(foo M3TA) y})', 'something %s (%s)' %
             ( primary, primary ) )

   @pm
   def testFindAllKeys( self ):
      def check( fStr, keyList ):
         self.assertEqual( find_all_meta_group_keys( prs( fStr ) ),
                           set( keyList ) )

      check( '', [] )
      check( '{(M3TA foo) x}', [ ( 'foo', ) ] )
      check( '{(M3TA foo) {(M3TA bar) x}}', [ ( 'foo', ), ( 'bar', ) ] )
      check( '{(M3TA foo) x} b {(M3TA bar) y}', [ ( 'foo', ), ( 'bar', ) ] )

   @pm
   def testUpdateAll( self ):
      filters = {
            '1': prs( '{(M3TA foo) new}' ),
            '2': prs( 'bla {(M3TA foo) old} x' )
         }

      update_all_meta_groups( filters )
      expected = {
            '1': prs( '{(M3TA foo) new}' ),
            '2': prs( 'bla {(M3TA foo) new} x' )
         }
      self.assertDictEqual( filters, expected )

      # updates within primaries
      filters = {
            '1': prs( '{(M3TA bar) newbarthing}' ),
            '2': prs( '{(M3TA foo) newfoothing {(M3TA bar) oldbarthing}}' ),
            '3': prs( 'xx {(M3TA foo) oldfoothig {(M3TA bar) olderbarthing}}' ),
         }

      self.maxDiff = None
      update_all_meta_groups( filters )
      expected = {
            '1': prs( '{(M3TA bar) newbarthing}' ),
            '2': prs( '{(M3TA foo) newfoothing {(M3TA bar) newbarthing}}' ),
            '3': prs( 'xx {(M3TA foo) newfoothing {(M3TA bar) newbarthing}}' ),
         }
      self.assertDictEqual( filters, expected )

   @pm
   def testUpdateAllErrors( self ):
      # Duplicate primaries
      filters = {
            '1': prs( '{(M3TA foo) new}' ),
            '2': prs( '{(M3TA foo) old}' )
         }
      self.assertRaises( TemplateError, update_all_meta_groups, filters )

      # No labels
      filters = {
            '1': prs( '{(M3TA) new}' ),
         }
      self.assertRaises( TemplateError, update_all_meta_groups, filters )

      # Missing key
      filters = {
            '1': prs( '{(M3TA foo) new}' ),
            '2': prs( 'x {(M3TA bar) old} {(M3TA baz) x}' )
         }
      self.assertRaises( TemplateError, update_all_meta_groups, filters )

if __name__ == '__main__':
   unittest.main()
