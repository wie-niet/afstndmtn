# usage:
import afstndmtn

# init api
api = afstndmtn.Api()

# search 
s = api.search(text='runforestrun')   # search for any text with 'runforestrun'
afstndmtn.Display( s )                # table view of search results


# first route from search results
r = s.result[0]                       
afstndmtn.Display( r )                # table view of route

# login
api.login('user', 'secret')
afstndmtn.Display( api.session )      # table view of session

# add to favorites:
api.tools.add_favorite(r)
afstndmtn.Display( api.favorite.refresh() )

# lookup favorites
api.favorite.search()                 # fetch favorites
afstndmtn.Display( api.favorite )     # table view of search results

# delete from favorites:
api.tools.delete_favorite(r)
afstndmtn.Display( api.favorite.refresh() )


# lookup private
api.private.search()                  # fetch private
afstndmtn.Display( api.private )      # table view of search results


# login
# api.logout()

#
# easy display command, handy for command line use or debugging:
# display Search/Route/Session object: afstndmtn.Display( obj )
#
afstndmtn.Display( s )               # table view of search results
afstndmtn.Display( r )               # table view of route
afstndmtn.Display( api.session )     # table view of session
