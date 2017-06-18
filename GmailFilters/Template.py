from __future__ import print_function
import re
import sys

from GmailFilters import FilterElement, ElementParser, ParseError, \
                         parse_filter_element

META_LABEL = 'M3TA'
META_PRIMARY_LABEL = 'M3TAP'

meta_regexp = re.compile( '^M3TAP?$' )

class TemplateError( Exception ):
   pass

def get_meta_group_key( elem, primaryOnly=False ):
   '''If elem is of the format of (M3TA x y z) or "META x y z",
   returns a sorted tuple of ('x', 'y', 'z').
   '''
   foundMeta = False
   if elem.delims == '()' and elem.has_sub_elems():
      tags = [ se.full_filter_str().strip() for se in elem.subElems ]
   elif elem.delims == '""':
      tags = elem.filterStr.split()
   else:
      return None

   if primaryOnly:
      foundMeta = META_PRIMARY_LABEL in tags
   else:
      foundMeta = any( filter( meta_regexp.match, tags ) )

   if not foundMeta:
      return None

   tags = [ t for t in tags if not meta_regexp.match( t ) ]
   if not tags:
      raise TemplateError( 'Template meta group has no labels: %s' %
                           elem.full_filter_str() )

   tags.sort()
   return tuple( tags )

def get_template_group_key( elem, primaryOnly=False ):
   if not elem.has_sub_elems() or elem.delims != '{}':
      return None

   metaKeyCnt = 0
   metaKey = None
   for subElem in elem.subElems:
      k = get_meta_group_key( subElem, primaryOnly=primaryOnly )
      if k is not None:
         if metaKey is None:
            metaKey = k
         else:
            raise TemplateError( "Multiple sibling meta keys found in '%s'" %
                                 str( elem ) )

   return metaKey

def is_template_or_group( elem, primaryOnly=False ):
   return get_template_group_key( elem, primaryOnly=primaryOnly ) is not None

def find_primary_template_group( filterElem ):
   orGroup = None
   nextElem = filterElem
   while orGroup is None:
      if not nextElem.has_sub_elems():
         return None
      if nextElem.delims == '{}':
         orGroup = nextElem
      else:
         if len( nextElem.subElems ) > 1:
            # The OR group is not the single group. It can only be like: (({}))
            return None
         nextElem = nextElem.subElems[ 0 ]

   assert orGroup
   if is_template_or_group( orGroup, primaryOnly=True ):
      return orGroup
   else:
      return None

def find_all_meta_group_keys( filterElem ):
   if not filterElem.has_sub_elems():
      return set()

   elemKey = get_meta_group_key( filterElem )
   if elemKey is not None:
      # This elem is a meta group key
      return set( [ elemKey ] )

   return set.union( *( find_all_meta_group_keys( se )
                     for se in filterElem.subElems ) )

def normalized_primary_elem( primaryElem ):
   pStr = primaryElem.full_filter_str()
   pStr = pStr.replace( META_PRIMARY_LABEL, META_LABEL )
   elem = parse_filter_element( pStr ).subElems[ 0 ]
   return elem

def sub_meta_groups( filterElem, primaryElem ):
   if not filterElem.has_sub_elems():
      return

   pMetaKey = get_template_group_key( primaryElem, primaryOnly=True )
   assert pMetaKey

   for i in range( len( filterElem.subElems ) ):
      k = get_template_group_key( filterElem.subElems[ i ] )
      if pMetaKey == k:
         pCopy = normalized_primary_elem( primaryElem )
         pCopy.preWs = filterElem.subElems[ i ].preWs
         pCopy.postWs = filterElem.subElems[ i ].postWs
         filterElem.subElems[ i ] = pCopy
      else:
         sub_meta_groups( filterElem.subElems[ i ], primaryElem )

def update_all_meta_groups( filterElemById ):
   primaryKeyToId = {}
   primaryKeyToGroup = {}

   for id_, filterElem in filterElemById.items():
      primaryGroup = find_primary_template_group( filterElem )
      if primaryGroup is None:
         continue
      key = get_template_group_key( primaryGroup, primaryOnly=True )
      assert key is not None

      if key in primaryKeyToId:
         raise TemplateError( "Primary key collision for %r between filters %s, %s" %
                              ( key, primaryKeyToId[ key ], id_ ) )
      primaryKeyToId[ key ] = id_
      primaryKeyToGroup[ key ] = primaryGroup

   for pKey, id_ in primaryKeyToId.items():
      for id2, filterElem in filterElemById.items():
         if id_ == id2:
            # Don't want to try to update the same filter
            continue

         sub_meta_groups( filterElem, primaryKeyToGroup[ pKey ] )

   allKeys = set()
   for id_, filterElem in filterElemById.items():
      allKeys |= find_all_meta_group_keys( filterElem )

   undefinedKeys = allKeys - set( primaryKeyToId.keys() )
   if undefinedKeys:
      raise TemplateError( "Could not find definition for keys: %s" %
                           ', '.join( str( k ) for k in undefinedKeys ) )
