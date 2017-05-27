from __future__ import print_function
import copy
import sys

from GmailFilters import FilterElement, ElementParser, ParseError

META_LABEL = 'M3TA'

class TemplateError( Exception ):
   pass

def get_meta_group_key( elem ):
   '''If elem is of the format of (M3TA x y z) or "META x y z",
   returns a sorted tuple of ('x', 'y', 'z').
   '''
   tags = []
   foundMeta = False
   if elem.delims == '()' and elem.has_sub_elems():
      for se in elem.subElems:
         if se.filterStr == META_LABEL:
            foundMeta = True
         else:
            tags.append( se.full_filter_str().strip() )
   elif elem.delims == '""':
      tags = elem.filterStr.split()
      foundMeta = META_LABEL in tags
      tags.remove( META_LABEL )

   if not foundMeta:
      return None
   if not tags:
      raise TemplateError( 'Template meta group has no labels: %s' %
                           elem.full_filter_str() )

   tags.sort()
   return tuple( tags )

def get_template_group_key( elem ):
   if not elem.has_sub_elems() or elem.delims != '{}':
      return None

   metaKeyCnt = 0
   metaKey = None
   for subElem in elem.subElems:
      k = get_meta_group_key( subElem )
      if k is not None:
         if metaKey is None:
            metaKey = k
         else:
            raise TemplateError( "Multiple sibling meta keys found in '%s'" %
                                 str( elem ) )

   return metaKey

def is_template_or_group( elem ):
   return get_template_group_key( elem ) is not None

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
   if is_template_or_group( orGroup ):
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

def sub_meta_groups( filterElem, primaryElem ):
   if not filterElem.has_sub_elems():
      return

   pMetaKey = get_template_group_key( primaryElem )
   assert pMetaKey

   for i in range( len( filterElem.subElems ) ):
      k = get_template_group_key( filterElem.subElems[ i ] )
      if pMetaKey == k:
         pCopy = copy.deepcopy( primaryElem )
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
      key = get_template_group_key( primaryGroup )
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
