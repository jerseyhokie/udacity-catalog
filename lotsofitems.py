from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Categories, Base, CategoryItems

engine = create_engine('sqlite:///catalog.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()



#A Sporting Goods Category
categories = Categories(name = "Sporting Goods")
session.add(categories)
session.commit()

categoriesItem1 = CategoryItems(name = "Basketball", description = "a round inflated ball, super exciting", categories = categories)
session.add(categoriesItem1)
session.commit()

categoriesItem2 = CategoryItems(name = "Baseball", description = "a round ball, extra super exciting", categories = categories)
session.add(categoriesItem2)
session.commit()

categoriesItem3 = CategoryItems(name = "Football", description = "an oblong inflated ball, sometimes less inflated to win!", categories = categories)
session.add(categoriesItem3)
session.commit()

categoriesItem4 = CategoryItems(name = "Soccerball", description = "a round inflated ball, a football outside the US", categories = categories)
session.add(categoriesItem4)
session.commit()

categoriesItem5 = CategoryItems(name = "Tennisball", description = "a round ball, fuzzzzzzzy", categories = categories)
session.add(categoriesItem5)
session.commit()


#A Books category
categories2 = Categories(name = "Books")
session.add(categories2)
session.commit()

categoriesItem1 = CategoryItems(name = "Grapes of Wrath", description = "Nothing to do with fruit", categories = categories2)
session.add(categoriesItem1)
session.commit()

categoriesItem2 = CategoryItems(name = "Cooking for Dummies", description = "Try not to burn things", categories = categories2)
session.add(categoriesItem2)
session.commit()

categoriesItem3 = CategoryItems(name = "A Brief History of Time", description = "Prevent Insomnia", categories = categories2)
session.add(categoriesItem3)
session.commit()

categoriesItem4 = CategoryItems(name = "Tesla: Part Deux", description = "A Biography of Elon Musk", categories = categories2)
session.add(categoriesItem4)
session.commit()

categoriesItem5 = CategoryItems(name = "Drinking Around the World", description = "All the things to drink in Epcot", categories = categories2)
session.add(categoriesItem5)
session.commit()

#A Movies Category
categories3 = Categories(name = "Movies")
session.add(categories3)
session.commit()

categoriesItem1 = CategoryItems(name = "Grapes of Wrath (1940)", description = "Nothing to do with fruit, the Motion Picture", categories = categories3)
session.add(categoriesItem1)
session.commit()

categoriesItem2 = CategoryItems(name = "A Wrinkle in Time", description = "Light / Dark / Shiny", categories = categories3)
session.add(categoriesItem2)
session.commit()

categoriesItem3 = CategoryItems(name = "Black Panther", description = "Wakanda!", categories = categories3)
session.add(categoriesItem3)
session.commit()

categoriesItem4 = CategoryItems(name = "Red Sparrow", description = "Spy Movie, think... Salt, Bond, Bourne", categories = categories3)
session.add(categoriesItem4)
session.commit()

categoriesItem5 = CategoryItems(name = "Tomb Raider", description = "Think: What is the limit of Remaking Something?", categories = categories3)
session.add(categoriesItem5)
session.commit()


print "added catalog items!"

