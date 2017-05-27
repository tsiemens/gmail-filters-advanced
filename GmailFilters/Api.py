from __future__ import print_function
import argparse
import copy
import os

import colors
import httplib2

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/gmail-python-quickstart.json
# SCOPES = 'https://www.googleapis.com/auth/gmail.readonly'
SCOPES = ' '.join( [
   'https://www.googleapis.com/auth/gmail.settings.basic ',
   'https://www.googleapis.com/auth/gmail.metadata' # for getProfile
   ] )

home_dir = os.path.expanduser( '~' )
config_dir = os.path.join( home_dir, '.gmail_filters' )

CLIENT_SECRET_FILE = os.path.join( config_dir, 'client_secret.json' )
APPLICATION_NAME = 'Gmail Filter Tools CLI'

credential_path = os.path.join( config_dir, 'credentials.json' )

def new_argparser_base( addHelp=True ):
   return argparse.ArgumentParser( parents=[ tools.argparser ], add_help=addHelp )

def get_credentials( flags ):
   """Gets valid user credentials from storage.

   If nothing has been stored, or if the stored credentials are invalid,
   the OAuth2 flow is completed to obtain the new credentials.

   Returns:
       Credentials, the obtained credential.
   """
   if not os.path.exists( config_dir ):
      os.makedirs( config_dir )

   store = Storage( credential_path )
   credentials = store.get()
   if not credentials or credentials.invalid:
      flow = client.flow_from_clientsecrets( CLIENT_SECRET_FILE, SCOPES )
      flow.user_agent = APPLICATION_NAME
      credentials = tools.run_flow( flow, store, flags )
      print( 'Storing credentials to ' + credential_path )
   return credentials

def get_auth_http( flags ):
   credentials = get_credentials( flags )
   return credentials.authorize( httplib2.Http() )

class Service( object ):
   def __init__( self, http, dryWrites=False ):
      self._service = discovery.build( 'gmail', 'v1', http=http )
      self.dryWrites = dryWrites

   def get_email_addr( self ):
      # pylint: disable=no-member
      results = self._service.users().getProfile( userId='me' ).execute()
      return results.get( 'emailAddress', None )

   def get_labels( self ):
      # pylint: disable=no-member
      results = self._service.users().labels().list( userId='me' ).execute()
      return results.get( 'labels', [] )

   def get_filter( self, filterId ):
      # pylint: disable=no-member
      return self._service.users().settings().filters().get( userId='me',
                                                             id=filterId ).execute()

   def get_filters( self ):
      # pylint: disable=no-member
      results = self._service.users().settings().filters().list( userId='me' ).execute()
      return results.get( 'filter', [] )

   def create_filter( self, filterObj ):
      if not self.dryWrites:
         # pylint: disable=no-member
         results = self._service.users().settings().filters()\
               .create( userId='me', body=filterObj ).execute()
         print( "create: %r" % ( results, ) )
      else:
         results = copy.deepcopy( filterObj )
         # The id is not the same, when returned from the server
         results[ 'id' ] = results[ 'id' ] + '_FAKE_NEW_ID'
         print( "DRY create: %r" % ( results, ) )
      return results

   def delete_filter( self, filterId ):
      if not self.dryWrites:
         # pylint: disable=no-member
         results = self._service.users().settings().filters()\
               .delete( userId='me', id=filterId ).execute()
         print( "delete: %r: %r" % ( filterId, results, ) )
      else:
         results = self.get_filter( filterId )
         print( "DRY delete %r: %r" % ( filterId, results, ) )
      return results

class Printer( object ):
   def __init__( self, service, color ):
      self.service = service
      self.color = color
      self.labelMap = None

   def maybe_color( self, msg, fg=None, style=None ):
      if self.color:
         return colors.color( msg, fg=fg, style=style )

      return msg

   def label_map( self ):
      if self.labelMap is None:
         self.labelMap = {}
         labels = self.service.get_labels()
         for label in labels:
            self.labelMap[ label[ 'id' ] ] = label[ 'name' ]

      return self.labelMap

   def print_filter( self, filter_, newFilter=None ):
      print( 'Filter %s:' % filter_[ 'id' ] )
      # Get all criteria keys, so we don't miss any, between the filter and
      # new filter if it is provided.
      criteriaKeys = set( filter_[ 'criteria' ].keys() )
      if newFilter is not None:
         criteriaKeys.update( newFilter[ 'criteria' ].keys() )

      # Print all criteria
      for k in criteriaKeys:
         v = filter_[ 'criteria' ].get( k )
         newValLine = None
         oldValStr = v if v is not None else repr( v )
         oldValLine = "  %s: %s" % ( k, oldValStr )

         if newFilter is not None:
            newValue = newFilter[ 'criteria' ].get( k )
            if newValue != v:
               oldValLine = self.maybe_color( '-' + oldValLine, fg='red' )
               oldValStr = repr( oldValStr )
               newValStr = newValue if newValue is not None else repr( newValue )
               newValLine = self.maybe_color( '+  %s: %s' % ( k, newValStr ),
                                              fg='green' )

         print( oldValLine )
         if newValLine is not None:
            print( newValLine )

      # This is cached, so it's ok to call it every time.
      labelIdsToName = self.label_map()
      # Print all actions to apply to the filter
      for k, v in filter_[ 'action' ].items():
         # Labels appear in a list, with the label id, which is not very useful
         # to read. Replace them with their readable name.
         if k == 'addLabelIds':
            for i in range( len( v ) ):
               if v[ i ] in labelIdsToName:
                  v[ i ] = labelIdsToName[ v[ i ] ]

         if isinstance( v, list ):
            v = ', '.join( str( x ) for x in v )

         print( "  -> %s: %s" % ( k, v ) )

