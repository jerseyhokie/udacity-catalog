from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Categories, Base, CategoryItems, User

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

# Create dummy user & my username
User1 = User(name="Robo Cataloger", email="Robby@cataloger.com",
             picture='https://pbs.twimg.com/profile_images/2671170543/18debd694829ed78203a5a36dd364160_400x400.png')
session.add(User1)
session.commit()

User2 = User(name="Chris Baines", email="cbaines78@gmail.com")
session.add(User2)
session.commit()

#A Sporting Goods Category
categories = Categories(user_id=1, name = "Sporting Goods")
session.add(categories)
session.commit()

categoriesItem1 = CategoryItems(user_id=1, name = "Basketball", description = "a round inflated ball, super exciting", categories = categories)
session.add(categoriesItem1)
session.commit()

categoriesItem2 = CategoryItems(user_id=1, name = "Baseball", description = "a round ball, extra super exciting", categories = categories)
session.add(categoriesItem2)
session.commit()

categoriesItem3 = CategoryItems(user_id=1, name = "Football", description = "an oblong inflated ball, sometimes less inflated to win!", categories = categories)
session.add(categoriesItem3)
session.commit()

categoriesItem4 = CategoryItems(user_id=1, name = "Soccerball", description = "a round inflated ball, a football outside the US", categories = categories)
session.add(categoriesItem4)
session.commit()

categoriesItem5 = CategoryItems(user_id=1, name = "Tennisball", description = "a round ball, fuzzzzzzzy", categories = categories)
session.add(categoriesItem5)
session.commit()


#A Books category
categories2 = Categories(user_id=2, name = "Books")
session.add(categories2)
session.commit()

categoriesItem1 = CategoryItems(user_id=2, name = "Grapes of Wrath", description = "Nothing to do with fruit", categories = categories2)
session.add(categoriesItem1)
session.commit()

categoriesItem2 = CategoryItems(user_id=2, name = "Cooking for Dummies", description = "Try not to burn things", categories = categories2)
session.add(categoriesItem2)
session.commit()

categoriesItem3 = CategoryItems(user_id=2, name = "A Brief History of Time", description = "Prevent Insomnia", categories = categories2)
session.add(categoriesItem3)
session.commit()

categoriesItem4 = CategoryItems(user_id=2, name = "Tesla: Part Deux", description = "A Biography of Elon Musk", categories = categories2)
session.add(categoriesItem4)
session.commit()

categoriesItem5 = CategoryItems(user_id=2, name = "Drinking Around the World", description = "All the things to drink in Epcot", categories = categories2)
session.add(categoriesItem5)
session.commit()

#A Movies Category
categories3 = Categories(user_id=1, name = "Movies")
session.add(categories3)
session.commit()

categoriesItem1 = CategoryItems(user_id=1, name = "Grapes of Wrath (1940)", description = "Nothing to do with fruit, the Motion Picture", categories = categories3)
session.add(categoriesItem1)
session.commit()

categoriesItem2 = CategoryItems(user_id=1, name = "A Wrinkle in Time", description = "Light / Dark / Shiny", categories = categories3)
session.add(categoriesItem2)
session.commit()

categoriesItem3 = CategoryItems(user_id=1, name = "Black Panther", description = "Wakanda!", categories = categories3)
session.add(categoriesItem3)
session.commit()

categoriesItem4 = CategoryItems(user_id=1, name = "Red Sparrow", description = "Spy Movie, think... Salt, Bond, Bourne", categories = categories3)
session.add(categoriesItem4)
session.commit()

categoriesItem5 = CategoryItems(user_id=1, name = "Tomb Raider", description = "Think: What is the limit of Remaking Something?", categories = categories3)
session.add(categoriesItem5)
session.commit()

print "added catalog items!"

